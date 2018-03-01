#!/usr/bin/env python2
# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import coloredlogs
import json
import logging
import os
import pkg_resources
import shutil
import sys
import tempfile
import threading
import time
from trello import TrelloApi

import cleanup
import command


# Initialize coloredlogs
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)
coloredlogs.DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
coloredlogs.install(level="INFO")

tmp_dir = None
module_dir = None


def parse_args(argv=None):
    """
    Argument parsing. Parses from sys.argv if argv is None.
    :param argv: argument vector to parse
    :return: parsed arguments
    """
    if argv is None:
        argv = sys.argv[1:]

    pkg_version = pkg_resources.require("trellosa")[0].version
    home = os.path.expanduser("~")

    # Set up the parent parser with shared arguments
    parser = argparse.ArgumentParser(prog="trellosa")
    parser.add_argument("--version", action="version", version="%(prog)s " + pkg_version)
    parser.add_argument("-d", "--debug",
                        help="Enable debug",
                        action="store_true")
    parser.add_argument("-w", "--workdir",
                        help="Path to working state directory",
                        type=os.path.abspath,
                        action="store",
                        default="%s/.trellosa" % home)
    parser.add_argument("-b", "--board",
                        help="Trello board ID to query (default: 5887b9767bc90fd832e669f8)",
                        action="store",
                        default="5887b9767bc90fd832e669f8")  # The Firefox board

    # Set up subparsers, one for each subcommand
    subparsers = parser.add_subparsers(help="Subcommand", dest="command")
    for command_name in command.all_commands:
        command_class = command.all_commands[command_name]
        sub_parser = subparsers.add_parser(command_name, help=command_class.help)
        command_class.setup_args(sub_parser)

    return parser.parse_args(argv)


tmp_dir = None


def __create_tempdir():
    """
    Helper function for creating the temporary directory.
    Writes to the global variable tmp_dir
    :return: Path of temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix='tlscanary_')
    logger.debug('Created temp dir `%s`' % temp_dir)
    return temp_dir


class RemoveTempDir(cleanup.CleanUp):
    """
    Class definition for cleanup helper responsible
    for deleting the temporary directory prior to exit.
    """
    @staticmethod
    def at_exit():
        global tmp_dir
        if tmp_dir is not None:
            logger.debug('Removing temp dir `%s`' % tmp_dir)
            shutil.rmtree(tmp_dir, ignore_errors=True)


# This is the entry point used in setup.py
def main(argv=None):
    global logger, tmp_dir, module_dir

    module_dir = os.path.split(__file__)[0]

    args = parse_args(argv)

    if args.debug:
        coloredlogs.install(level='DEBUG')

    logger.debug("Command arguments: %s" % args)

    cleanup.init()
    tmp_dir = __create_tempdir()

    # Create workdir (usually ~/.trellosa, used for caching etc.)
    # Assumes that no previous code must write to it.
    if not os.path.exists(args.workdir):
        logger.debug('Creating working directory %s' % args.workdir)
        os.makedirs(args.workdir)

    # Execute the specified command
    try:
        result = command.run(args, tmp_dir)

    except KeyboardInterrupt:
        logger.critical("\nUser interrupt. Quitting...")
        return 10

    if len(threading.enumerate()) > 1:
        logger.info("Waiting for background threads to finish")
        while len(threading.enumerate()) > 1:
            logger.debug("Remaining threads: %s" % threading.enumerate())
            time.sleep(2)

    return result


if __name__ == "__main__":
    sys.exit(main(sys.argv))
