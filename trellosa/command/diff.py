# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import jsondiff
import logging
from pprint import PrettyPrinter as pp
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer
import sys

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class DiffMode(BaseCommand):
    """
    Command for visualizing changes between trello board snapshots
    """

    name = "diff"
    help = "Show differences between snapshots"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-a", "--from",
                            dest="a_ref",
                            help="Snapshot baseline reference for comparison (default: 1, latest snapshot)",
                            action="store",
                            default="1")
        parser.add_argument("-b", "--to",
                            dest="b_ref",
                            help="Snapshot reference for comparing against (default: 0, online)",
                            action="store",
                            default="0")
        parser.add_argument("-e", "--everything",
                            help="Do not filter noisy, irrelevant changes",
                            action="store_true")
        parser.add_argument("-f", "--format",
                            help="Output format (default: pretty)",
                            choices=["jdiff", "json", "pretty"],
                            action="store",
                            default="pretty")
        parser.add_argument("-t", "--token",
                            help="Override Trello token",
                            action="store")

    def run(self):
        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        a_handle, a = snapshots.get(self.args, snapshot_db, tag_db, self.args.a_ref)
        if a_handle is None:
            logger.critical("Invalid baseline reference (-a --from)")
            return 5
        if a is None:
            logger.critical("Error retrieving baseline content")
            return 5

        b_handle, b = snapshots.get(self.args, snapshot_db, tag_db, self.args.b_ref)
        if b_handle is None:
            logger.critical("Invalid target reference (-b --to)")
            return 5
        if b is None:
            logger.critical("Error retrieving target content")
            return 5

        logger.debug("Diffing %s and %s" % (a_handle, b_handle))

        # Unless marshal=True is given, jsondiff.diff() produces dicts with non-string
        # keys which json.dump() does not like at all.
        diff = jsondiff.diff(a, b, syntax="symmetric", marshal=True)

        # Filter out obvious changelings
        if "meta" in diff and "snapshot_time" in diff["meta"]:
            del diff["meta"]["snapshot_time"]
            if len(diff["meta"]) == 0:
                del diff["meta"]

        if len(diff) == 0:
            return 0

        if not self.args.everything:
            # Filter out irrelevant and noisy changes

            for l in diff["labels"].keys():
                if "uses" in diff["labels"][l]:
                    del diff["labels"][l]["uses"]
                if len(diff["labels"][l]) == 0:
                    del diff["labels"][l]
            if len(diff["labels"]) == 0:
                del diff["labels"]

            for c in diff["cards"].keys():
                if "labels" in diff["cards"][c]:
                    del diff["cards"][c]["labels"]
                if "badges" in diff["cards"][c]:
                    del diff["cards"][c]["badges"]
                if "uses" in diff["cards"][c]:
                    del diff["cards"][c]["uses"]
                if "idLabels" in diff["cards"][c]:
                    del diff["cards"][c]["idLabels"]
                if "dateLastActivity" in diff["cards"][c]:
                    del diff["cards"][c]["dateLastActivity"]
                if len(diff["cards"][c]) == 0:
                    del diff["cards"][c]
            if len(diff["cards"]) == 0:
                del diff["cards"]

        if len(diff) == 0:
            logger.warning("Hiding irrelevant changes. Use `--everything` to see then.")
            return 0

        if self.args.format == "jdiff":
            print diff
        elif self.args.format == "json":
            diff_str = json.dumps(diff, indent=4, sort_keys=True)
            if sys.stdout.isatty():
                print highlight(diff_str, JsonLexer(), Terminal256Formatter())
            else:
                print diff_str
        if self.args.format == "pretty":
            # py3 knows os.get_terminal_size(), but we need to guesstimate a width in py2
            pp(indent=1, width=120).pprint(diff)

        return 1
