# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from requests.exceptions import HTTPError
import time
import re


logger = logging.getLogger(__name__)


def generate_token_url():
    return "https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey"


class BugzillaClient(object):
    # FIXME use production url---v
    URL = "https://bugzilla-dev.allizom.org/rest/bug"
    # TODO use production url -^

    def __init__(self, token=None):
        self.token = token

    @staticmethod
    def generate_token_url():
        return generate_token_url()

    def check_token(self, token):
        return type(token) is str and token.isalnum() and 30 < len(token) < 50

    def set_token(self, token):
        self.token = token

    def get_snapshot(self):
        params = {
            "include_fields": "_all", # could also be "id,summary,status,url,version,target_milestone"
            "component": "Security: Review Requests",
            "product": "Firefox",
            "api_key": self.token
        }
        response = requests.get(self.URL, params=params)

        response.raise_for_status()

        bugs = response.json()['bugs']
        if len(bugs) == 0:
            raise HTTPError("Could not find any bugs at all.")

        now = time.time()
        meta = {"snapshot_time": now}

        return {"meta": meta, "bugs": bugs, "whatever": "else"}

    def parse_version(self, listname):
        """ parses version information from name of a trello list"""
        pattern = 'F(irefo)?x\s?([4-9]{1}[0-9]{1})'
        match = re.search(pattern, listname)
        if match:
            return match.group(2)

    def create_bug(self, card_id, trello_snapshot):
        card = trello_snapshot['cards'][card_id]
        #labels = trello_snapshot['labels'][card_id]
        listobj = trello_snapshot['lists'][card['idList']]

        version = self.parse_version(listobj['name'])

        bugdata = {
            'groups': ['mozilla-employee-confidential'],
            'version': "{} Branch".format(version),
            'target_milestone': "Firefox {}".format(version),
            'url': card['shortUrl'],
            'summary': 'Risk Assessment: ' + card['name'],
            "description": "Risk Assessment for {}\n\n{}".format(card['name'], card['shortUrl']),
            "component": "Security: Review Requests",
            "product": "Firefox",
            "keywords": ["rra"],
            "api_key": self.token
        }

        return DraftBug(self.URL, bugdata)


class DraftBug():
    def __init__(self, url, data):
        self.url = url
        self.params = data

    def __str__(self):
        return "Bug '{}' for version {}".format(
            self.params['summary'],
            self.params['target_milestone'])

    def preview_verbose(self):
        return self.params

    def submit(self):
        """ Creates a new bug and returns its URL """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.post(self.url, json=self.params, headers=headers)
        response.raise_for_status()

        bugid = response.json()['id']

        # https://bugzilla.mozilla.org/show_bug.cgi?id=
        showbugurl = self.url.replace("rest/bug", "show_bug.cgi?id=")
        return showbugurl + bugid


