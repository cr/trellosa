# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
from trellosa.token import read_token, write_token, generate_token_url, check_token


logger = logging.getLogger(__name__)


class SetupMode(BaseCommand):
    """
    Command for configuring Trello access
    """

    name = "setup"
    help = "Configure Trello access"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-i", "--interactive",
                            help="Run interactive setup",
                            action="store_true")
        parser.add_argument("-t", "--token",
                            help="Set Trello token as new default",
                            action="store")

    def run(self):

        if self.args.token:
            if not check_token(self.args.token, write=True):
                logger.critical("Invalid or read-only token")
                return 10
            else:
                logger.info("Writing new token")
                write_token(self.args.token, self.args.workdir)
                return 0

        configured_token = read_token(self.args.workdir)

        if self.args.interactive:
            if check_token(configured_token):
                logger.warning("Trello access setup already completed. Current token will be overwritten")
            url = generate_token_url()
            logger.info("Go to `%s`, authorize a token, and give it to me" % url)
            while True:
                token_candidate = raw_input("Token: ").strip()
                if check_token(token_candidate, write=True):
                    write_token(token_candidate, self.args.workdir)
                    logger.info("Token stored successfully")
                    return 0
                else:
                    logger.error("Invalid token")

        if configured_token is None:
            logger.info("No Trello access token configured, yet")
            url = generate_token_url()
            logger.info("Go to `%s` to authorize a new token and pass it with the `--token` argument" % url)
            return 1

        if check_token(configured_token, write=True):
            logger.warning("Trello access setup already completed")
            url = generate_token_url()
            logger.info("If you need a new token, go to `%s` and pass it with the `--token` argument" % url)
            return 0

        if check_token(configured_token, write=False):
            logger.warning("Read-only token found")
            url = generate_token_url()
            logger.info("Go to `%s` to authorize a new token and pass it with the `--token` argument" % url)
            return 1

        else:
            logger.error("Trello access token is already configured, but invalid")
            url = generate_token_url()
            logger.info("If you need a new token, go to `%s` and pass it with the `--token` argument" % url)
            return 5
