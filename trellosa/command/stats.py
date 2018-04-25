# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from basecommand import BaseCommand
import trellosa.snapshots as snapshots
import trellosa.tags as tags


logger = logging.getLogger(__name__)


class StatsMode(BaseCommand):
    """
    Command for listing board snapshots
    """

    name = "stats"
    help = "Produce various board and bug statistics"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-s", "--snapshot",
                            help="Reference snapshot (default: 1, latest)",
                            action="store",
                            default="1")
        parser.add_argument("-t", "--token",
                            help="Override Trello token",
                            action="store")
        parser.add_argument("-a", "--all",
                            help="Show info for closed lists, too",
                            action="store_true")

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

        result = {}

        # Just Focusing on trello for now
        # TODO: implement Bugzilla stats
        content = content["firefox_trello"]

        for lid in content["lists"]:
            if content["lists"][lid]["closed"] and not self.args.all:
                continue
            if content["lists"][lid]["name"].startswith("About:"):
                continue
            sec_label_counts = {}
            num_cards = 0
            num_inactive_cards = 0
            for cid in content["cards"]:
                if content["cards"][cid]["idList"] != lid:
                    continue
                if content["cards"][cid]["closed"]:
                    num_inactive_cards += 1
                    continue
                num_cards += 1
                c = content["cards"][cid]
                has_sec_label = False
                for l in c["labels"]:
                    if l["name"].startswith("Security Triage:"):
                        has_sec_label = True
                        if l["name"] not in sec_label_counts:
                            sec_label_counts[l["name"]] = 1
                        else:
                            sec_label_counts[l["name"]] += 1
                        if l["name"] not in ["Security Triage: OK", "Security Triage: Action required"]:
                            logger.warning("Unknown label `%s` on card `%s`" % (l["name"], c["shortUrl"]))
                if not has_sec_label:
                    logger.warning("Card without security label in `%s`: `%s` `%s`"
                                   % (content["lists"][lid]["name"][:20] + "...", c["name"], c["shortUrl"]))

            sec_ok = sec_label_counts["Security Triage: OK"] if "Security Triage: OK" in sec_label_counts else 0
            sec_action = sec_label_counts["Security Triage: Action required"] \
                if "Security Triage: Action required" in sec_label_counts else 0
            sec_missing = num_cards - sec_ok - sec_action
            l = content["lists"][lid]
            result[lid] = {
                "__name": l["name"],
                "_closed": l["closed"],
                "active_cards": num_cards,
                "inactive_cards": num_inactive_cards,
                "security_label_ok": sec_ok,
                "security_label_action": sec_action,
                "security_label_missing": sec_missing
            }

        snapshots.json_highlight_print(result)

        return 0
