# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer
import sys

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class LogMode(BaseCommand):
    """
    Command for listing board snapshots
    """

    name = "log"
    help = "Query and maintain the snapshop database"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-s", "--show",
                            help="Dump a board snapshot to the terminal",
                            action="store")

    def run(self):

        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        if self.args.show is None:
            handle_list = snapshot_db.list()
            length = len(handle_list)
            for number in xrange(length):
                ref = length - number
                handle = handle_list[number]
                tag_list = tag_db.handle_to_tags(handle)
                if len(tag_list) == 0:
                    print "%d: %s" % (ref, handle)
                else:
                    print "%d: %s [%s]" % (ref, handle, ",".join(tag_list))
        else:
            handle, content = snapshots.get(self.args, snapshot_db, tag_db, self.args.show)
            if handle is None:
                logger.critical("Invalid snapshot reference (-s --show)")
                return 5
            if content is None:
                logger.critical("Error retrieving snapshot content")
                return 5

            content_str = json.dumps(content, indent=4, sort_keys=True)
            if sys.stdout.isatty():
                print highlight(content_str, JsonLexer(), Terminal256Formatter())
            else:
                print content_str

        return 0
