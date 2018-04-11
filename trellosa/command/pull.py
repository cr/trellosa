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
from trellosa.trello import FirefoxTrello
from trellosa.token import read_token


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
        user_token = read_token(self.args.workdir, override=self.args.token)
        if user_token is None:
            logger.critical("No Trello access token configured. Use `setup` command or `--token` argument")
            return 10

        tr = FirefoxTrello(user_token=user_token, board_id=self.args.board)
        data = tr.get_snapshot()
        if data is None:
            return 5

        if self.args.dump:
            sys.stdout.write(json.dumps(data, indent=4, sort_keys=True))
            sys.stdout.flush()
        else:
            db = snapshots.SnapshotDB(self.args)
            handle = datetime.datetime.utcfromtimestamp(data["meta"]["snapshot_time"]).strftime("%Y-%m-%dZ%H-%M-%S")
            data = json.dumps(data, sort_keys=True)
            logger.info("Writing snapshot `%s`" % handle)
            db.write(handle, data)

        return 0
