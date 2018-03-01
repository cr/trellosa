# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

logger = logging.getLogger(__name__)


def token_config_file_name(workdir):
    return os.path.join(workdir, "token.txt")


def generate_token_url(tr):
    return tr.get_token_url("TrelloSA", expires="never", write_access=False)


def is_valid_token(tr, token):
    if token is not None and len(token) == 64 and token.isalnum():
        try:
            tr.set_token(token)
            return True
        except Exception:  # FIXME: Wrongly assuming that invalid tokens throw. Find working test.
            return False
    else:
        return False


def write_token(token, workdir):
    file_name = token_config_file_name(workdir)
    with open(file_name, "w") as f:
        os.chmod(file_name, 0600)
        f.write(token)


def read_token(workdir):
    file_name = token_config_file_name(workdir)
    try:
        with open(file_name, "r") as f:
            os.chmod(file_name, 0600)
            return f.readline().strip()
    except IOError:
        return None
