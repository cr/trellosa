# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import jsondiff
import logging

from basecommand import BaseCommand
from pull import fetch
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
        parser.add_argument("-t", "--token",
                            help="Override Trello token",
                            action="store")

    def run(self):
        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)
        snaps = snapshot_db.list()

        a_ref = self.args.a_ref
        a_handle = None
        if a_ref == "0":
            a_handle = "online"
        elif a_ref.isdigit():
            try:
                a_handle = snaps[-int(a_ref)]
            except IndexError:
                a_handle = None
        elif a_ref in snaps:
            a_handle = a_ref
        elif tag_db.exists(a_ref):
            a_handle = tag_db.tag_to_handle(a_ref)
        if a_handle is None:
            logger.critical("Invalid baseline reference (-a --from)")
            return 5

        b_ref = self.args.b_ref
        b_handle = None
        if b_ref == "0":
            b_handle = "online"
        elif b_ref.isdigit():
            try:
                b_handle = snaps[-int(b_ref)]
            except IndexError:
                b_handle = None
        elif b_ref in snaps:
            b_handle = b_ref
        elif tag_db.exists(b_ref):
            b_handle = tag_db.tag_to_handle(b_ref)
        if b_handle is None:
            logger.critical("Invalid target reference (-b --to)")
            return 5

        logger.debug("Diffing %s and %s" % (a_handle, b_handle))

        if a_handle == "online":
            a = fetch(self.args)
        else:
            a = json.loads(snapshot_db.read(a_handle))
        if a is None:
            return 5

        if b_handle == "online":
            b = fetch(self.args)
        else:
            b = json.loads(snapshot_db.read(b_handle))
        if b is None:
            return 5

        # cards = b["cards"]
        # lists = b["lists"]
        #
        # old_cards = a["cards"]
        # old_lists = a["lists"]
        #
        # old_card_ids = set(old_cards.keys())
        # old_list_ids = set(old_lists.keys())
        #
        # card_ids = set(cards.keys())
        # list_ids = set(lists.keys())
        #
        # dropped_card_ids = old_card_ids - card_ids
        # new_card_ids = card_ids - old_card_ids
        #
        # dropped_list_ids = old_list_ids - list_ids
        # new_list_ids = list_ids - old_list_ids

        # sys.stdout.write(json.dumps(jsondiff.diff(a, b, dump=True)))
        # sys.stdout.flush()

        diff = jsondiff.diff(a, b, syntax="symmetric")
        if "meta" in diff and "snapshot_time" in diff["meta"]:
            del diff["meta"]["snapshot_time"]
            if len(diff["meta"]) == 0:
                del diff["meta"]

        if len(diff) == 0:
            return 0

        from pprint import pprint as pp
        pp(diff)

        return 5
