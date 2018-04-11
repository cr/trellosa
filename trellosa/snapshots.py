# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import gzip
import json
import logging
import os

from trellosa.token import read_token
from trellosa.trello import FirefoxTrello


logger = logging.getLogger(__name__)


class SnapshotDB(object):
    """
    Class to manage on-disk snapshots
    """

    def __init__(self, args):
        self.args = args
        self.snap_dir = os.path.abspath(os.path.join(args.workdir, "snapshots"))
        if not os.path.isdir(self.snap_dir):
            os.makedirs(self.snap_dir)

    def handle_to_file_name(self, handle):
        """
        Converts a snapshot handle to its file name
        :param handle: str with handle
        :return: str with file name
        """
        # handle format is .strftime("%Y-%m-%dZ%H-%M-%S")
        year, month, _, _, _ = handle.split("-")
        return os.path.join(self.snap_dir, year, month, "%s.gz" % handle)

    @staticmethod
    def file_name_to_handle(file_name):
        """
        Converts snapshot file name to its handle
        :param file_name: str
        :return: str with handle
        """
        return os.path.splitext(os.path.basename(file_name))[0]

    def exists(self, handle):
        """
        Check whether snapshot handle is valid
        :param handle: str with handle
        :return: bool
        """
        matches = glob.glob(os.path.join(self.snap_dir, "2???", "??", "%s.gz" % handle))
        return len(matches) > 0

    def list_snapshots(self):
        """
        Returns a list of available snapshot files
        :return: list of str of file names
        """
        return glob.glob(os.path.join(self.snap_dir, "2???", "??", "2???-??-??*"))

    def list(self):
        """
        Returns a list of snapshot handles
        :return: list of str of snapshot handles
        """
        return [self.file_name_to_handle(file_name) for file_name in self.list_snapshots()]

    def delete(self, handle):
        """
        Delete a snapshot specified by its handle. All associated
        files are purged from the database. There is no undo.
        :param handle: str with snapshot handle
        :return: None
        """
        global logger
        file_name = self.handle_to_file_name(handle)
        logger.debug("Purging `%s` from run snapshot database" % file_name)
        os.remove(file_name)

    def open(self, handle, mode="r"):
        """
        Open a snapshot file by handle and part name
        :param handle: str log handle
        :param mode: str file mode
        :return: file object
        """
        global logger

        file_name = self.handle_to_file_name(handle)
        if "w" in mode and not os.path.isdir(os.path.dirname(file_name)):
            os.makedirs(os.path.dirname(file_name))

        logger.debug("Opening snapshot file `%s` in mode `%s`" % (file_name, mode))

        try:
            return gzip.open(file_name, mode)
        except IOError as err:
            raise Exception("Error opening snapshot file for handle `%s`: %s" % (handle, err))

    def read(self, handle):
        """
        Return the string content of a snapshot referenced by its handle
        :param handle: str with handle
        :return: str with content of snapshot
        """
        global logger
        logger.debug("Reading snapshot `%s`" % handle)
        with self.open(handle, "r") as f:
            return f.read().decode("utf-8")

    def write(self, handle, data):
        """
        Write snapshot referenced by handle and part.
        The data object will be passed through str().encode("utf-8").
        :param handle: str with handle
        :param data: object to write
        :return: None
        """
        global logger
        logger.debug("Writing snapshot `%s`" % handle)
        with self.open(handle, "w") as f:
            f.write(str(data).encode("utf-8"))


def match(snapshot_db, tag_db, ref):
    snaps = snapshot_db.list()

    handle = None
    if ref == "0":
        handle = "online"
    elif ref.isdigit():
        try:
            handle = snaps[-int(ref)]
        except IndexError:
            handle = None
    elif ref in snaps:
        handle = ref
    elif tag_db.exists(ref):
        handle = tag_db.tag_to_handle(ref)

    return handle


def get(args, snapshot_db, tag_db, ref):
    handle = match(snapshot_db, tag_db, ref)
    if handle is None:
        return None, None

    if handle == "online":
        user_token = read_token(args.workdir, override=args.token)
        if user_token is None:
            logger.critical("No Trello access token configured. Use `setup` command or `--token` argument")
            raise Exception("Unable to continue without token")
        tr = FirefoxTrello(user_token=user_token, board_id=args.board)
        return handle, tr.get_snapshot()
    else:
        return handle, json.loads(snapshot_db.read(handle))
