# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from requests.exceptions import HTTPError
import time


logger = logging.getLogger(__name__)


def generate_token_url(app_key, token_name="TrelloSA", expiration="never", scope="read,write"):
    url = "https://trello.com/1/authorize?" \
          "key={key}&name={name}&expiration={expiration}&response_type={type}&scope={scope}"
    args = {
        "key": app_key,
        "name": token_name,
        "expiration": expiration,
        "type": "token",
        "scope": scope
    }
    return url.format(**args)


class TrelloClient(object):

    BASE_URL = "https://trello.com/1"
    TRELLO_APP_KEY = "fee6885be0783a3f421d5998840da9cb"

    def __init__(self, app_key=TRELLO_APP_KEY, user_token=None, base_url=BASE_URL):
        self.app_key = app_key
        self.user_token = user_token
        self.base_url = base_url

    def generate_token_url(self, expiration="never", scope="read,write"):
        return generate_token_url(self.TRELLO_APP_KEY, expiration=expiration, scope=scope)

    def check_token(self, user_token, write=False):
        if user_token is None or len(user_token) != 64 or not user_token.isalnum():
            return False
        try:
            info = self.get("/tokens/{}".format(user_token))
        except HTTPError as e:
            if e.errno == 404:
                return False
        if info["identifier"] != "TrelloSA":
            return False
        board_permissions = filter(lambda x: x["modelType"] == "Board", info["permissions"])[0]
        if write:
            logger.debug("Token provides write access")
            return board_permissions["read"] and board_permissions["write"]
        else:
            logger.warning("Token provides no write permission")
            return board_permissions["read"]

    def set_token(self, user_token):
        self.user_token = user_token

    def get(self, method, **kwargs):
        """
        Make an authenticated GET request and return parsed JSON result.

        Generally used for retrieving Trello objects.
        """
        url = "{}/{}".format(self.BASE_URL, method.lstrip("/"))
        params = kwargs
        params.update({"key": self.app_key, "token": self.user_token})
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, method, json=None, **kwargs):
        """
        Make an authenticated POST request and return parsed JSON result.

        Generally used for creating Trello objects.
        """
        url = "{}/{}".format(self.BASE_URL, method.lstrip("/"))
        data = kwargs
        data.update({"key": self.app_key, "token": self.user_token})
        r = requests.post(url, json=json, data=data)
        r.raise_for_status()
        return r.json()

    def put(self, method, json=None, **kwargs):
        """
        Make an authenticated PUT request and return parsed JSON result.

        Generally used for updating Trello objects.
        """
        url = "{}/{}".format(self.BASE_URL, method.lstrip("/"))
        params = kwargs
        params.update({"key": self.app_key, "token": self.user_token})
        r = requests.put(url, json=json, params=params)
        r.raise_for_status()
        return r.json()

    def delete(self, method, **kwargs):
        """
        Make an authenticated DELETE request and return parsed JSON result.

        Generally used for deleting Trello objects.
        """
        url = "{}/{}".format(self.BASE_URL, method.lstrip("/"))
        params = kwargs
        params.update({"key": self.app_key, "token": self.user_token})
        r = requests.delete(url, params=params)
        r.raise_for_status()
        return r.json()

    def batch_get(self, methods):
        methods = list(methods)  # Ensuring that we're not touching the parameter object
        results = []
        while len(methods) > 0:
            # Trello batches are limited to 10 requests which must be prefixed with a /
            urls = ",".join(["/" + method if not method.startswith("/") else method for method in methods[:10]])
            results.append(self.get("/batch/", urls=urls))
            methods = methods[min(len(methods), 10):]
        return results


class FirefoxTrello(TrelloClient):

    FIREFOX_BOARD_ID = "5887b9767bc90fd832e669f8"

    # Fixme: These IDs change when you use a different board, even if it's a copy of the original
    SECURITY_NOTES_ID = "5a986701d6afbd6de1c283ab"
    LABEL_ACTION_REQUIRED = "5a87103058c87cee7a848645"
    LABEL_OK = "5aa1d077f70408344daa5d80"

    def __init__(self, user_token=None, board_id=FIREFOX_BOARD_ID):
        super(FirefoxTrello, self).__init__(user_token=user_token)
        self.board_id = board_id
        self.board = None
        self.labels = None
        self.custom_fields = None

    def get_board(self):
        return self.get("/boards/{}".format(self.board_id))

    def get_labels(self, caching=True):
        if self.labels is None or not caching:
            result = self.get("/boards/{}/labels".format(self.board_id))
            self.labels = dict(map(lambda x: (x["id"], x), result))
        return self.labels

    def get_custom_fields(self, caching=True):
        if self.custom_fields is None or not caching:
            result = self.get("/boards/{}/customFields".format(self.board_id))
            self.custom_fields = dict(map(lambda x: (x["id"], x), result))
        return self.custom_fields

    def get_cards(self):
        result = self.get("/boards/{}/cards/all".format(self.board_id), customFieldItems="true")
        return dict(map(lambda x: (x["id"], x), result))

    def get_card(self, card_id):
        return self.get("/cards/{}".format(card_id), customFieldItems="true")

    def get_lists(self):
        result = self.get("/boards/{}/lists/all".format(self.board_id))
        return dict(map(lambda x: (x["id"], x), result))

    def get_snapshot(self):
        now = time.time()
        board = self.get_board()
        labels = self.get_labels()
        custom_fields = self.get_custom_fields()
        lists = self.get_lists()
        cards = self.get_cards()
        meta = {"board": board, "snapshot_time": now}

        return {"meta": meta, "cards": cards, "lists": lists, "labels": labels, "custom_fields": custom_fields}

    def set_custom_field_text(self, card_id, field_id, text):
        data = {"value": {"text": text}}
        self.put("/card/{}/customField/{}/item".format(card_id, field_id), json=data)

    def set_security_notes(self, card_id, message):
        return self.set_custom_field_text(card_id, self.SECURITY_NOTES_ID, message)

    def set_security_ok_label(self, card_id):
        self.post("/cards/{}/idLables")
        pass

    def set_security_action_required_label(self, card_id):
        pass