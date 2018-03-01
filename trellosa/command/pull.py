# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import logging
from requests.exceptions import HTTPError
import sys
import time
from trello import TrelloApi

from basecommand import BaseCommand
from trellosa import TRELLO_PUBLIC_APP_KEY
from trellosa.token import read_token,is_valid_token
import trellosa.snapshots as snapshots


logger = logging.getLogger(__name__)


def fetch(args):
    tr = TrelloApi(TRELLO_PUBLIC_APP_KEY)

    user_token = read_token(args.workdir)

    if args.token is not None:
        if is_valid_token(tr, args.token):
            logger.warning("Overriding default Trello token")
            user_token = args.token
        else:
            logger.critical("Invalid token specified")
            return None

    if user_token is None:
        logger.critical("No Trello access token configured. Use `setup` command or `--token` argument")
        return None

    tr.set_token(user_token)

    now = time.time()
    board_id = args.board
    try:
        board = tr.boards.get(board_id)
    except HTTPError as e:
        logger.error(e)
        return None

    cards = dict(map(lambda x: [x["id"], x], tr.boards.get_card(board_id)))
    lists = dict(map(lambda x: [x["id"], x], map(tr.lists.get, set(map(lambda c: c["idList"], cards.itervalues())))))
    meta = {"board": board, "snapshot_time": now}

    return {"meta": meta, "cards": cards, "lists": lists}


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

        data = fetch(self.args)
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
