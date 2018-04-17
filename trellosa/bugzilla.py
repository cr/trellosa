# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from requests.exceptions import HTTPError
import time


logger = logging.getLogger(__name__)


def generate_token_url():
    return "https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey"


class BugzillaClient(object):
    URL = "https://bugzilla.mozilla.org/rest/bug"

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
        if not response.status_code == 200:
            raise HTTPError("Status was not 200. Meh.")

        bugs = response.json()['bugs']
        if len(bugs) == 0:
            raise HTTPError("Could not find any bugs at all.")

        now = time.time()
        meta = {"snapshot_time": now}

        return {"meta": meta, "bugs": bugs, "whatever": "else"}

    def create_bug(self, card_id, trello_snapshot):
        # FIXME: needs implementation
        pass
