# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import re
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


def parse_firefox_version(list_name):
    m = re.search(r'''(fx|firefox)\s*(\d+)''', list_name, flags=re.I)
    if m is None:
        return None
    else:
        return m.group(2)


def extract_security_info(card, security_notes_id):
    if "customFieldItems" in card:
        for cf in card["customFieldItems"]:
            if cf["idCustomField"] == security_notes_id:
                return cf["value"]["text"]
    return None


def extract_bugzilla_bug(card, security_notes_id):
    sec_info = extract_security_info(card, security_notes_id)
    if sec_info is None:
        return None
    m = re.search(r'''(bug)\s*(\d+)''', sec_info, flags=re.I)
    if m is None:
        return None
    else:
        return m.group(2)


def extract_security_labels(card, security_action_required_label, security_ok_label):
    labels = []
    if "labels" in card:
        for label in card["labels"]:
            if label["id"] == security_action_required_label:
                labels.append(security_action_required_label)
                continue
            if label["id"] == security_ok_label:
                labels.append(security_ok_label)
    return labels


def security_label_should_be(bug, security_action_required_label, security_ok_label):
    # FIXME: implement function that returns security label according to bug state
    status = bug["status"]
    resolution = bug["resolution"]
    if status == "NEW" or status == "REOPENED":
        return security_action_required_label
    elif status == "UNCONFIRMED":
        return security_action_required_label
    elif status == "ASSIGNED":
        return security_action_required_label
    elif status == "RESOLVED":
        if resolution == "FIXED":
            return security_ok_label
        elif resolution == "INVALID":
            return security_ok_label
        elif resolution == "INCOMPLETE":  #TODO: This seems to be non-standard
            logger.warn("http://bugzil.la/%s has weird bug resolution %s" % (bug["id"], resolution))
            return security_ok_label
        elif resolution == "WONTFIX":
            return security_ok_label  #TODO: We may want to use a different trello card label here
        else:
            logger.error("http://bugzil.la/%s has weird bug resolution %s" % (bug["id"], resolution))
            return security_action_required_label
    else:
        logger.error("http://bugzil.la/%s has weird bug status %s" % (bug["id"], status))
        return security_action_required_label


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

    def __init__(self, user_token=None, board_id=FIREFOX_BOARD_ID):
        super(FirefoxTrello, self).__init__(user_token=user_token)
        self.board_id = board_id
        self.board = None
        self.labels = None
        self.__custom_fields = None
        self.__security_notes = None
        self.__security_action_required_label = None
        self.__security_ok_label = None
        self.__security_notes_id = None

    def get_board(self):
        return self.get("/boards/{}".format(self.board_id))

    def get_labels(self, caching=True):
        if self.labels is None or not caching:
            result = self.get("/boards/{}/labels".format(self.board_id))
            self.labels = dict(map(lambda x: (x["id"], x), result))
        return self.labels

    @property
    def custom_fields(self):
        if self.__custom_fields is None:
            result = self.get("/boards/{}/customFields".format(self.board_id))
            self.__custom_fields = dict(map(lambda x: (x["id"], x), result))
        return self.__custom_fields

    @property
    def security_notes_id(self):
        if self.__security_notes_id is None:
            for field in self.custom_fields.itervalues():
                if field["name"].lower() == "Security Notes".lower():
                    self.__security_notes_id = field["id"]
                    break
            if self.__security_notes_id is None:
                raise Exception("Custom field `Security Notes` is gone, can't live without it")
        return self.__security_notes_id

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
        lists = self.get_lists()
        cards = self.get_cards()
        meta = {"board": board, "snapshot_time": now}

        return {"meta": meta, "cards": cards, "lists": lists, "labels": labels, "custom_fields": self.custom_fields}

    def set_custom_field_text(self, card_id, field_id, text):
        data = {"value": {"text": text}}
        self.put("/card/{}/customField/{}/item".format(card_id, field_id), json=data)

    def set_security_notes(self, card_id, message):
        return self.set_custom_field_text(card_id, self.security_notes_id, message)

    def set_security_ok_label(self, card_id):
        self.post("/cards/{}/idLabels".format(card_id), value=self.security_ok_label)
        self.delete("/cards/{}/idLabels/{}".format(card_id, self.security_action_required_label))

    def set_security_action_required_label(self, card_id):
        self.post("/cards/{}/idLabels".format(card_id), value=self.security_action_required_label)
        self.delete("/cards/{}/idLabels/{}".format(card_id, self.security_ok_label))

    def __update_labels(self):
        labels = self.get_labels()
        for label in labels.itervalues():
            if label["name"].lower() == "Security Triage: OK".lower():
                self.__security_ok_label = label["id"]
            elif label["name"].lower() == "Security Triage: Action required".lower():
                self.__security_action_required_label = label["id"]
        if self.__security_ok_label is None:
            raise Exception("Label `Security Triage: OK` is gone, can't live without it")
        if self.__security_action_required_label is None:
            raise Exception("Label `Security Triage: Action required` is gone, can't live without it")

    @property
    def security_action_required_label(self):
        if self.__security_action_required_label is None:
            self.__update_labels()
        return self.__security_action_required_label

    @property
    def security_ok_label(self):
        if self.__security_ok_label is None:
            self.__update_labels()
        return self.__security_ok_label
