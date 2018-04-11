# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from IPython import embed

from basecommand import BaseCommand
from trellosa.trello import FirefoxTrello
import trellosa.snapshots as snapshots
import trellosa.tags as tags
from trellosa.token import read_token

logger = logging.getLogger(__name__)


class Shell(BaseCommand):
    """
    Command that drops you into an authenticated IPython session
    """

    name = "shell"
    help = "Play with the API in an authenticated IPython environment"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-t", "--token",
                            help="Override Trello token",
                            action="store")

    def run(self):
        user_token = read_token(self.args.workdir, override=self.args.token)
        if user_token is None:
            logger.warning("No token configured")

        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)
        tr = FirefoxTrello(user_token=user_token, board_id=self.args.board)

        user_token = read_token(self.args.workdir)

        if self.args.token is not None:
            if tr.check_token(self.args.token, write=False):
                logger.warning("Overriding default Trello token")
                user_token = self.args.token
            else:
                logger.critical("Invalid token specified")
                return 5

        if user_token is None:
            logger.critical("No Trello access token configured. Use `setup` command or `--token` argument")
            return 5

        tr.set_token(user_token)

        embed()

        return 0
