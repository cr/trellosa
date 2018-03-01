# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class TagMode(BaseCommand):
    """
    Command for managing tags
    """

    name = "tag"
    help = "Manage snapshot tags"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-a", "--add",
                            help="Tag to add",
                            action="store")
        parser.add_argument("-r", "--remove",
                            help="Tag to remove",
                            action="store")
        parser.add_argument("-s", "--snapshot",
                            help="Snapshot reference (default: 1, latest snapshot)",
                            action="store")

    def run(self):

        tag_db = tags.TagsDB(self.args)
        snapshot_db = snapshots.SnapshotDB(self.args)

        if self.args.add is not None:
            tag = self.args.add
            if not tag_db.is_valid_tag(tag):
                logger.critical("Invalid tag")
                return 5
            handle = self.args.snapshot
            if handle is None:
                handle = "1"
            if handle.isdigit():
                handle = snapshot_db.list()[-int(handle)]
            if not snapshot_db.exists(handle):
                logger.critical("Invalid snapshot reference")
            logger.info("Setting `%s` tag for snapshot `%s`" % (tag, handle))
            tag_db.add(tag, handle)

        elif self.args.remove is not None:
            tag = self.args.remove
            if not tag_db.is_valid_tag(tag):
                logger.critical("Invalid tag")
                return 5
            logger.info("Removing `%s` tag" % tag)
            tag_db.delete(self.args.remove)

        else:
            if self.args.snapshot is None:
                for tag in tag_db.list():
                    print "%s\t%s" % (tag, tag_db.tag_to_handle(tag))
            else:
                print "%s\t%s" % (self.args.snapshot, ",".join(tag_db.handle_to_tags(self.args.snapshot)))

        return 0
