# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import logging
import sys


from basecommand import BaseCommand
import trellosa.snapshots as snapshots


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
        parser.add_argument("-t", "--token",
                            help="Override Trello token",
                            action="store")

    def run(self):

        data = snapshots.fetch(self.args.workdir, self.args.token, self.args.board)
        if data is None:
            return 5

        if self.args.dump:
            sys.stdout.write(json.dumps(data, indent=4, sort_keys=True))
            sys.stdout.flush()
        else:
            db = snapshots.SnapshotDB(self.args)
            handle = datetime.datetime.utcfromtimestamp(data["meta"]["snapshot_time"]).strftime("%Y-%m-%dZ%H-%M-%S")
            data = json.dumps(data)
            logger.info("Writing snapshot `%s`" % handle)
            db.write(handle, data)

        return 0
