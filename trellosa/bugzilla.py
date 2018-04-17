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
    return "https://bugzilla.mozilla.org/machmirntoken"


class BugzillaClient(object):

    def __init__(self, token=None):
        self.token = token

    @staticmethod
    def generate_token_url():
        return generate_token_url()

    def check_token(self, token):
        # FIXME: implement proper check
        return type(token) is str and token.isalnum() and 30 < len(token) < 50

    def set_token(self, token):
        self.token = token

    def get_snapshot(self):
        # FIXME: needs implementation
        now = time.time()
        meta = {"snapshot_time": now}
        bugs = []

        return {"meta": meta, "bugs": bugs, "whatever": "else"}

    def create_bug(self, card_id, trello_snapshot):
        # FIXME: needs implementation
        pass
