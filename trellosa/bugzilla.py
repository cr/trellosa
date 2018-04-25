# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from requests.exceptions import HTTPError
import time
import re

from trellosa.trello import parse_firefox_version


logger = logging.getLogger(__name__)


def generate_token_url():
    return "https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey"


class BugzillaClient(object):
    # FIXME use production url---v
    # URL = "https://bugzilla-dev.allizom.org/rest/bug"
    API_URL = "https://bugzilla.mozilla.org/rest"
    # TODO use production url -^

    def __init__(self, token=None):
        self.token = token
        self.__firefox_product_id = None
        self.__firefox_versions = None
        self.__firefox_milestones = None

    @staticmethod
    def generate_token_url():
        return generate_token_url()

    @staticmethod
    def check_token(token):
        return type(token) is str and token.isalnum() and 30 < len(token) < 50

    def set_token(self, token):
        self.token = token

    def get_snapshot(self):
        params = {
            "include_fields": "_all", # could also be "id,summary,status,url,version,target_milestone"
            "component": "Security: Review Requests",
            "product": "Firefox"
        }
        result = self.get("bug", **params)

        bugs = dict([(str(x["id"]), x) for x in result['bugs']])
        if len(bugs) == 0:
            raise HTTPError("Could not find any bugs at all.")

        now = time.time()
        meta = {
            "snapshot_time": now,
            "milestones": self.firefox_milestones,
            "versions": self.firefox_versions
        }

        return {"meta": meta, "bugs": bugs}

    def create_bug(self, card_id, trello_snapshot):
        card = trello_snapshot['cards'][card_id]
        # labels = trello_snapshot['labels'][card_id]
        listobj = trello_snapshot['lists'][card['idList']]
        parsed_version = parse_firefox_version(listobj['name'])
        bugdata = self.map_firefox_version(parsed_version)
        bugdata.update({
            "groups": ["mozilla-employee-confidential"],
            "url": card["shortUrl"],
            "summary": "Risk Assessment: " + card["name"],
            "description": "Risk Assessment for {}\n\n{}".format(card["name"], card["shortUrl"]),
            "component": "Security: Review Requests",
            "product": "Firefox",
            "whiteboard": "rra"
        })

        return DraftBug(self, bugdata, parsed_version)

    def request(self, method, call, json=None, params=None):
        """Perform authenticated request, return response as JSON or log errors"""
        logger.debug("""BugzillaClient.request(method="%s", call="%s", json="%s", params="%s") called"""
                     % (method, call, json, params))
        if params is None:
            params = {}
        if self.token is not None and "api_key" not in params:
            params["api_key"] = self.token
        url = "%s/%s" % (self.API_URL, call.lstrip("/"))
        response = requests.request(method, url, json=json, params=params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(str(e))
            text = response.text
            if len(text) > 1000:
                text = text[:1000] + "..."
            logger.debug("%s response was: `%s`" % (method.upper(), text))
            raise e
        return response.json()

    def get(self, call, json=None, **params):
        """Convenience wrapper for authenticated GET requests"""
        return self.request("GET", call, params=params)

    def post(self, call, params=None, **json):
        """Convenience wrapper for authenticated POST requests"""
        return self.request("POST", call, json=json, params=params)

    def put(self, call, params=None, **json):
        """Convenience wrapper for authenticated PUT requests"""
        return self.request("PUT", call, json=json, params=params)

    def valid_values(self, field_name, product=None):
        if product is None:
            product_id = self.firefox_product_id
        else:
            product_id = self.get_product_id(product)
        result = self.get("field/bug/%s/%s/values" % (field_name, product_id))
        return result["values"]

    def get_product_id(self, product_name):
        result = self.get("product", names=[product_name])
        return result["products"][0]["id"]

    @property
    def firefox_product_id(self):
        # if self.__firefox_product_id is None:
        #     self.__firefox_product_id = self.get_product_id("Firefox")
        # return self.__firefox_product_id
        return 21  # Unlikely to ever change

    @property
    def firefox_milestones(self):
        if self.__firefox_milestones is None:
            self.__firefox_milestones = self.valid_values("target_milestone")
        return list(self.__firefox_milestones)

    @property
    def firefox_versions(self):
        if self.__firefox_versions is None:
            self.__firefox_versions = self.valid_values("version")
        return list(self.__firefox_versions)

    def map_firefox_version(self, firefox_version):
        version = "%s Branch" % str(firefox_version)
        if version not in self.firefox_versions:
            assert "Trunk" in self.firefox_versions
            version = "Trunk"

        target_milestone = "Firefox %s" % str(firefox_version)
        if target_milestone not in self.firefox_milestones:
            assert "Future" in self.firefox_milestones
            target_milestone = "Future"

        return {"version": version, "target_milestone": target_milestone}

    def update(self, bug_id, **json):
        # Updating bugs requires special request body formatting.
        # See http://bugzilla.readthedocs.io/en/latest/api/core/v1/bug.html#update-bug
        self.put("bug/%s" % bug_id, **json)

    def update_version(self, bug_id, firefox_version):
        version_spec = self.map_firefox_version(firefox_version)
        self.update(bug_id, **version_spec)

    def update_url(self, bug_id, url):
        url_spec = {"url": url}
        self.update(bug_id, **url_spec)


class DraftBug(object):
    def __init__(self, bz, bugdata, firefox_version=None):
        self.bz = bz
        self.bugdata = bugdata
        self.firefox_version = firefox_version

    def __str__(self):
        return "Bug '{}' for version {}".format(
            self.bugdata['summary'],
            self.bugdata['target_milestone'])

    def __getitem__(self, item):
        return self.bugdata[item]

    def __setitem__(self, key, value):
        self.bugdata[key] = value

    def preview_verbose(self):
        return dict(self.bugdata)

    def submit(self):
        """ Creates a new bug and returns its URL """
        response = self.bz.post("bug", json=self.bugdata)
        print response.text
        response.raise_for_status()
        return str(response.json()['id'])
