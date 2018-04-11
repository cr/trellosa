# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from trellosa.trello import TrelloClient


logger = logging.getLogger(__name__)


def token_config_file_name(workdir):
    return os.path.join(workdir, "token.txt")


def write_token(token, workdir):
    file_name = token_config_file_name(workdir)
    with open(file_name, "w") as f:
        os.chmod(file_name, 0600)
        f.write(token)


def read_token(workdir, override=None):
    if override is None:
        file_name = token_config_file_name(workdir)
        try:
            with open(file_name, "r") as f:
                os.chmod(file_name, 0600)
                return f.readline().strip()
        except IOError:
            return None
    else:
        tr = TrelloClient()
        if tr.check_token(override, write=False):
            return override
        else:
            return None


def generate_token_url(expiration="never", scope="read,write"):
    tr = TrelloClient()
    return tr.generate_token_url(expiration=expiration, scope=scope)


def check_token(user_token, write=True):
    tr = TrelloClient()
    return tr.check_token(user_token, write=write)
