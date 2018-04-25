# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from IPython import embed

from basecommand import BaseCommand
from trellosa.bugzilla import BugzillaClient
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

    def run(self):
        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        trello_token = read_token(self.args.workdir, token_type="trello")
        if trello_token is None:
            logger.critical("No Trello access token configured. Use `setup` command first")
            raise Exception("Unable to continue without token")
        tr = FirefoxTrello(user_token=trello_token)

        bz_token = read_token(self.args.workdir, token_type="bugzilla")
        if bz_token is None:
            logger.critical("No Bugzilla access token configured. Use `setup` command first")
            raise Exception("Unable to continue without token")
        bz = BugzillaClient(token=bz_token)

        snapshot = snapshots.get(self.args, snapshot_db, tag_db, "1")

        embed()

        return 0
