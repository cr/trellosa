# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import re

from basecommand import BaseCommand
from trellosa.bugzilla import BugzillaClient
import trellosa.snapshots as snapshots
import trellosa.tags as tags
import trellosa.token as token
from trellosa.trello import parse_firefox_version, extract_bugzilla_bug, extract_security_info, \
    extract_security_labels, security_label_should_be, FirefoxTrello


logger = logging.getLogger(__name__)


class TriageMode(BaseCommand):
    """
    Command for triaging bugs
    """

    name = "triage"
    help = "Triage bugs by diffing snapshots"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-a", "--from",
                            dest="a_ref",
                            help="Snapshot baseline reference for comparison (default: `triaged` tag)",
                            action="store",
                            default="triaged")
        parser.add_argument("-b", "--to",
                            dest="b_ref",
                            help="Snapshot reference for comparing against (default: 0, online)",
                            action="store",
                            default="0")
        parser.add_argument("-m", "--mode",
                            help="Output format (default: interactive)",
                            choices=["interactive", "json"],
                            action="store",
                            default="interactive")
        # parser.add_argument("-n", "--dry-run",
        #                     help="Don't change anything, just print what would be changed",
        #                     action="store_true")
        parser.add_argument("--all",
                            help="Also consider Trello cards already present during last triage",
                            action="store_true")

    def run(self):
        snapshot_db = snapshots.SnapshotDB(self.args)
        tag_db = tags.TagsDB(self.args)

        bz_token = token.read_token(self.args.workdir, token_type="bugzilla")
        if bz_token is None:
            logger.critical("No Bugzilla access token configured. Use `setup` command first")
            return 10

        bz = BugzillaClient(bz_token)

        tr_token = token.read_token(self.args.workdir, token_type="trello")
        if tr_token is None:
            logger.critical("No Trello access token configured. Use `setup` command first")
            return 10

        tr = FirefoxTrello(user_token=tr_token)

        a_handle, a = snapshots.get(self.args, snapshot_db, tag_db, self.args.a_ref)
        if a_handle is None:
            if self.args.a_ref == "triaged":
                logger.critical("You might want to tag the base snapshot to compare against as `triaged` first")
            else:
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

        # Just a few shortcuts for terser code
        aft = b["firefox_trello"]
        bft = b["firefox_trello"]
        abz = b["bugzilla"]
        bbz = b["bugzilla"]

        if self.args.mode == "json":
            from IPython import embed
            embed()
            return 0

        # FIXME: Internal state is not updated during operations. Hence full syncronization
        # may require multiple passes.

        # Create a new bug for every (relevant) card that is not associated to one, yet.
        for cid, card in bft["cards"].iteritems():

            # Check whether there are strange security notes
            sec_note = extract_security_info(card, tr.security_notes_id)
            if sec_note is not None and not sec_note.startswith("bug "):
                logger.warning("Card %s has strange security note format: `%s`" % (card["shortUrl"], sec_note))

            if cid in aft["cards"]:
                from_card = aft["cards"][cid]
                from_list = aft["lists"][from_card["idList"]]
            else:
                from_card = None
                from_list = None
            to_list = bft["lists"][card["idList"]]
            labels = [l["name"] for l in card["labels"]]
            bug_id = extract_bugzilla_bug(card, tr.security_notes_id)
            if bug_id is not None and bug_id not in bbz["bugs"]:
                logger.warning("Bug http://bugzil.la/%s referenced by Trello card %s, but not among bug list"
                               % (bug_id, card["shortUrl"]))
            firefox_version = parse_firefox_version(to_list["name"])

            # Don't add bugs for cards that were around last triage, unless called with --all
            if cid in aft["cards"] and not self.args.all:
                logger.debug("Skipping card `%s` which was already triaged last time" % card["shortUrl"])
                continue

            card_info = {
                "id": card["id"],
                "name": card["name"],
                "labels": labels,
                "description": card["desc"][:300] + "...",
                "list_from": from_list["name"],
                "list_in": to_list["name"],
                "card_url": card["shortUrl"],
                "bug": bug_id
            }

            if bug_id is None:
                if to_list["name"] == "About:This Board":
                    continue
                if to_list["name"] == "Backlog" and not self.args.all:
                    # Skip if card is not relevant
                    logger.debug("Ignoring card %s" % card["shortUrl"])
                else:
                    # Create new bug
                    if firefox_version is None:
                        print "Bugless card %s in list `%s`:" % (card["shortUrl"], to_list["name"])
                    else:
                        print "Bugless card %s for Firefox version %s:" % (card["shortUrl"], firefox_version)
                    snapshots.json_highlight_print([card_info])
                    print "The corresponding bug data is:"
                    bug = bz.create_bug(cid, bft)
                    bug_preview = bug.preview_verbose()
                    snapshots.json_highlight_print([bug_preview])
                    yes_or_no = raw_input("Do you want to create a bug with that data in Bugzilla? (y/N) ")
                    if yes_or_no.lower().startswith("y"):
                        bug_id = bug.submit()
                        logger.critical("Created bug http://bugzil.la/%s" % bug_id)
                        logger.info("Updating security note and label on Trello card %s" % card["shortUrl"])
                        tr.set_security_notes(card["id"], "bug %s" % bug_id)
                        tr.set_security_action_required_label(card["id"])
                    else:
                        logger.warning("Skipping bug creation")

        # Syncronize Bugzilla version / target milestone to Trello state.
        # Trello state is authoritative.

        short_url_map = {None: None, "": None}
        for cid, card in bft["cards"].iteritems():
            short_url_map[card["shortUrl"]] = card

        for bid, bug in bbz["bugs"].iteritems():

            # Sometimes bugs still have long Trello URLs
            card_url = None
            m = re.match(r"""(https://trello.com/c/[A-Za-z0-9]+)(/.*)*""", bug["url"])
            if m is not None:
                card_url = m.group(1)
                if m.group(2) is not None:
                    logger.debug("Bug http://bugzil.la/%s `%s` has long Trello URL" % (bid, bug["summary"]))

            card = short_url_map[card_url]
            if card is None:
                logger.warn("Bug http://bugzil.la/%s `%s` is not associated with a Trello card"
                             % (bid, bug["summary"]))
                # snapshots.json_highlight_print(bug)
                # Look through Trello cards and see if one links to this bug
                associated_cards = []
                for card in bft["cards"].itervalues():
                    if extract_bugzilla_bug(card, tr.security_notes_id) == str(bid):
                        associated_cards.append(card)
                if len(associated_cards) == 1:
                    logger.info("Trello card `%s` %s is associated with https://bugzil.la/%s"
                                % (associated_cards[0]["name"], associated_cards[0]["shortUrl"], bid))
                    yes_or_no = raw_input("Do you want to update the bug's URL field? (y/N) ")
                    if yes_or_no.lower().startswith("y"):
                        bz.update_url(bid, card["shortUrl"])
                    else:
                        logger.warn("https://bugzil.la/%s not updated" % bid)
                elif len(associated_cards) > 1:
                    associated_urls = [c["shortUrl"] for c in associated_cards]
                    logger.warn("Multiple cards point to https://bugzil.la/%s: %s" % (bid, associated_urls))
                    raw_input("Press return to continue.")
                continue
            card_bug = bz.create_bug(card["id"], bft)
            old_version = bug["version"]
            old_milestone = bug["target_milestone"]
            new_version = card_bug["version"]
            new_milestone = card_bug["target_milestone"]
            if old_version != new_version or old_milestone != new_milestone:
                logger.warn("Version mismatch for bug http://bugzil.la/%s" % bid)
                print "Bugzilla state:"
                snapshots.json_highlight_print([bug])
                print "Bug according to Trello state:"
                snapshots.json_highlight_print([card_bug.bugdata])
                yes_or_no = raw_input("Do you want to update the bug from `%s / %s` to `%s / %s`? (y/N) "
                                      % (old_version, old_milestone, new_version, new_milestone))
                if yes_or_no.lower().startswith("y"):
                    logger.debug("Updating bug %s to version %s" % (bid, card_bug.firefox_version))
                    bz.update_version(bid, card_bug.firefox_version)
                else:
                    logger.info("Skipping version update for bug http://bugzil.la/%s" % bid)

        # TODO: Syncronize Trello labels to Bugzilla bug state.
        # Bugzilla state is authoritative.

        for cid, card in bft["cards"].iteritems():
            bid = extract_bugzilla_bug(card, tr.security_notes_id)
            if bid is None:
                continue
            try:
                bug = bbz["bugs"][bid]
            except KeyError:
                logger.warn("Card `%s` references unfetched bug http://bugzil.la/%s" % (card["shortUrl"], bid))
                continue
            if bug["resolution"] == "DUPLICATE":
                logger.debug("Skipping duplicate bug http://bugzil.la/%s" % bid)
                continue
            label_is = extract_security_labels(card, tr.security_action_required_label, tr.security_ok_label)
            label_should = security_label_should_be(bug, tr.security_action_required_label, tr.security_ok_label)
            if label_is == [label_should]:
                continue
            print card["shortUrl"], "http://bugzil.la/%s" % bid, label_is, label_should
            if label_should == tr.security_action_required_label:
                if label_is == [tr.security_ok_label]:
                    logger.warn("Card %s has triage label `OK`, but should have `Action required`" % card["shortUrl"])
                else:
                    logger.warn("Card %s has no triage label and should have `Action required`" % card["shortUrl"])
                yes_or_no = raw_input("Do you want to update the card? (y/N) ")
                if yes_or_no.lower().startswith("y"):
                    tr.set_security_action_required_label(card["id"])
            elif label_should == tr.security_ok_label:
                if label_is == [tr.security_action_required_label]:
                    logger.warn("Card %s has triage label `Action required`, but should have `OK`" % card["shortUrl"])
                else:
                    logger.warn("Card %s has no triage label and should have `OK`" % card["shortUrl"])
                yes_or_no = raw_input("Do you want to update the card? (y/N) ")
                if yes_or_no.lower().startswith("y"):
                    tr.set_security_ok_label(card["id"])
            else:
                logger.error("Internal error with card %s / bug http://bugzil.la/%s" % (card["shortUrl"], bug["id"]))
                raise Exception("Internal error")

        return 0
