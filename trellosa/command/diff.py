# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import jsondiff
import logging
import os
from pprint import PrettyPrinter as pp

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

        # TODO: Adapt filtering to new trello + bugzilla combo snapshots

        # Filter out obvious changelings
        if "meta" in diff and "snapshot_time" in diff["meta"]:
            del diff["meta"]["snapshot_time"]
            if len(diff["meta"]) == 0:
                del diff["meta"]

        if len(diff) == 0:
            return 0

        if not self.args.everything:
            # Filter out irrelevant and noisy changes

            if "labels" in diff:
                for l in diff["labels"].keys():
                    if "uses" in diff["labels"][l]:
                        del diff["labels"][l]["uses"]
                    if len(diff["labels"][l]) == 0:
                        del diff["labels"][l]
                if len(diff["labels"]) == 0:
                    del diff["labels"]

            if "cards" in diff:
                for c in diff["cards"].keys():
                    if "desc" in diff["cards"][c]:
                        del diff["cards"][c]["desc"]
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
            logger.warning("Irrelevant changes hidden. Use `--everything` to see them.")
            return 0

        if self.args.format == "jdiff":
            print diff
        elif self.args.format == "json":
            snapshots.json_highlight_print(diff)
        if self.args.format == "pretty":
            # py3 knows os.get_terminal_size(), but we need to guesstimate a width in py2
            try:
                width = os.get_terminal_size().columns
            except AttributeError:
                width = 120
            except OSError:
                width = 120
            pp(indent=1, width=str(width)).pprint(diff)

        return 1
