# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class QueryMode(BaseCommand):
    """
    Command for querying Trello or Bugzilla IDs
    """

    name = "query"
    help = "Query specific Trello or Bugzilla IDs"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for query-specific arguments.

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
        for p in content:
            for k in content[p]:
                logger.debug("Searching in `%s`" % k)
                if tid in content[p][k]:
                    logger.debug("Direct hit for `%s` in `%s`" % (tid, k))
                    result = {p: {k: {tid: content[p][k][tid]}}}
                    break
                for kk in content[p][k]:
                    logger.debug("Checking against `%s`" % kk)
                    if tid in kk:
                        logger.debug("Matched `%s` in %s `%s`" % (tid, k, kk))
                        if p not in result:
                            result[p] = {}
                        if k not in result[p]:
                            result[p][k] = {}
                        result[p][k][kk] = content[p][k][kk]

        snapshots.json_highlight_print(result)

        return 0
