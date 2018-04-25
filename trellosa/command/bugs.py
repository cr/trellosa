# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
import trellosa.bugzilla as bugzilla
from trellosa.snapshots import json_highlight_print
import trellosa.token as token

logger = logging.getLogger(__name__)


class BugsMode(BaseCommand):
    """
    Command for listing board snapshots
    """

    name = "bugs"
    help = "Query RRA-related bugzilla bugs"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-d", "--dummy",
                            help="Just an unused dummy arg",
                            action="store")
        parser.add_argument("-t", "--token",
                            help="Override Bugzilla token",
                            action="store")

    def run(self):

        bz_token = token.read_token(self.args.workdir, token_type="bugzilla")
        if bz_token is None:
            logger.critical("No Bugzilla access token configured. Use `setup` command or `--token` argument")
            return 10

        bz = bugzilla.BugzillaClient(bz_token)
        content = bz.get_snapshot()
        json_highlight_print(content)

        return 0
