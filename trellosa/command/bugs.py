# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer
import sys

from basecommand import BaseCommand
import trellosa.bugzilla as bugzilla
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
        # FIXME: sample implementation

        bz_token = token.read_token(self.args.workdir, override=self.args.token, token_type="bugzilla")
        if bz_token is None:
            logger.critical("No Bugzilla access token configured. Use `setup` command or `--token` argument")
            return 10

        bz = bugzilla.BugzillaClient(bz_token)
        content = bz.get_snapshot()

        import trellosa.snapshots as snapshots
        import trellosa.tags as tags

        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)
        handle, trello_snapshot = snapshots.get(self.args, snapshot_db, tag_db, "1")

        draftbug = bz.create_bug("596e8cfb5126ab3b6fe254a7",
                                 trello_snapshot)
        print draftbug
        print

        draftbug.submit()

        content_str = json.dumps(content, indent=4, sort_keys=True)
        if sys.stdout.isatty():
            print highlight(content_str, JsonLexer(), Terminal256Formatter())
        else:
            print content_str

        return 0
