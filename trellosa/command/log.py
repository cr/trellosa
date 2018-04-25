# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

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
        Add subparser for log-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-s", "--show",
                            help="Dump a snapshot to the terminal",
                            action="store")

        parser.add_argument("--delete",
                            help="Delete a snapshot",
                            action="store")

    def run(self):

        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        if self.args.delete:
            handle = snapshots.match(snapshot_db, tag_db, self.args.delete)
            if handle is None:
                logger.critical("Unknown reference for deletion")
                return 10
            elif handle == "online":
                logger.critical("Deleting the Internet...")
                logger.warn("Done. You are on your own now. Please start over.")
                return 42
            else:
                snapshot_db.delete(handle)
                # TODO: Also delete associated tags
                return 0

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

            snapshots.json_highlight_print(content)

        return 0
