# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class PullMode(BaseCommand):
    """
    Command for capturing board snapshots
    """

    name = "pull"
    help = "Capture trello board snapshots"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-d", "--dump",
                            help="Just dump online board state to terminal as JSON",
                            action="store_true")

    def run(self):
        tag_db = tags.TagsDB(self.args)
        snapshot_db = snapshots.SnapshotDB(self.args)
        _, snapshot = snapshots.get(self.args, snapshot_db, tag_db, "0")  # handle 0 is current online state

        if self.args.dump:
            snapshots.json_highlight_print(snapshot)
        else:
            snapshots.store(snapshot_db, snapshot)

        return 0
