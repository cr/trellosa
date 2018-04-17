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
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class QueryMode(BaseCommand):
    """
    Command for listing board snapshots
    """

    name = "query"
    help = "Query specific Trello IDs"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-s", "--snapshot",
                            help="Reference snapshot (default: 1, latest snapshot)",
                            action="store",
                            default="1")
        parser.add_argument("-i", "--id",
                            help="ID to query",
                            action="store")

    def run(self):

        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        handle, content = snapshots.get(self.args, snapshot_db, tag_db, self.args.snapshot)
        if handle is None:
            logger.critical("Invalid snapshot reference (-s --show)")
            return 5
        if content is None:
            logger.critical("Error retrieving snapshot content")
            return 5

        if self.args.id is None:
            logger.critical("Please specify ID to query with `-i`")
            return 10

        tid = str(self.args.id)
        logger.debug("Looking for ID pattern `%s`" % tid)

        result = {}
        for k in content:
            logger.debug("Searching in `%s`" % k)
            if tid in content[k]:
                logger.debug("Direct hit for `%s` in `%s`" % (tid, k))
                result = {k: {tid: content[k][tid]}}
                break
            for kk in content[k]:
                logger.debug("Checking against `%s`" % kk)
                if tid in kk:
                    logger.debug("Matched `%s` in %s `%s`" % (tid, k, kk))
                    if k not in result:
                        result[k] = {}
                    result[k][kk] = content[k][kk]

        result_str = json.dumps(result, indent=4, sort_keys=True)
        if sys.stdout.isatty():
            print highlight(result_str, JsonLexer(), Terminal256Formatter())
        else:
            print result_str

        return 0
