# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from trellosa.bugzilla import BugzillaClient
from trellosa.trello import TrelloClient

logger = logging.getLogger(__name__)


def token_config_file_name(workdir, token_type="trello"):
    return os.path.join(workdir, "%s_token.txt" % token_type)


def write_token(token, workdir, token_type="trello"):
    file_name = token_config_file_name(workdir, token_type)
    with open(file_name, "w") as f:
        os.chmod(file_name, 0600)
        f.write(token)


def read_token(workdir, override=None, token_type="trello"):
    if override is None:
        file_name = token_config_file_name(workdir, token_type)
        try:
            with open(file_name, "r") as f:
                os.chmod(file_name, 0600)
                return f.readline().strip()
        except IOError:
            return None
    else:
        if token_type == "trello":
            tr = TrelloClient()
            if tr.check_token(override, write=False):
                return override
            else:
                return None
        elif token_type == "bugzilla":
            bz = BugzillaClient()
            if bz.check_token(override):
                return override
            else:
                return None
        else:
            return None


def generate_token_url(token_type="trello"):
    if token_type == "trello":
        tr = TrelloClient()
        return tr.generate_token_url(expiration="never", scope="read,write")
    elif token_type == "bugzilla":
        bz = BugzillaClient()
        return bz.generate_token_url()
    else:
        raise Exception("unsupported topken type")


def check_token(user_token, token_type="trello"):
    if token_type == "trello":
        tr = TrelloClient()
        return tr.check_token(user_token, write=True)
    elif token_type == "bugzilla":
        bz = BugzillaClient()
        return bz.check_token(user_token)
    else:
        return False
