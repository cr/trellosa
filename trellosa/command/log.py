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

    def run(self):
        db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)
        handle_list = db.list()
        length = len(handle_list)
        for number in xrange(length):
            ref = length - number
            handle = handle_list[number]
            tag_list = tag_db.handle_to_tags(handle)
            if len(tag_list) == 0:
                print "%d: %s" % (ref, handle)
            else:
                print "%d: %s [%s]" % (ref, handle, ",".join(tag_list))
