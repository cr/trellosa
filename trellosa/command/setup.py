# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
from trello import TrelloApi

from basecommand import BaseCommand
from trellosa.token import generate_token_url, is_valid_token, read_token, write_token
from trellosa import TRELLO_PUBLIC_APP_KEY


logger = logging.getLogger(__name__)


class SetupMode(BaseCommand):
    """
    Command for configuring Trello access
    """

    name = "setup"
    help = "Configure Trello access"

    @classmethod
    def setup_args(cls, parser):
        """
        Add subparser for setup-specific arguments.

        :param parser: parent argparser to add to
        :return: None
        """

        parser.add_argument("-i", "--interactive",
                            help="Run interactive setup",
                            action="store_true")
        parser.add_argument("-t", "--token",
                            help="Set Trello token as new default",
                            action="store")

    def run(self):
        tr = TrelloApi(TRELLO_PUBLIC_APP_KEY)

        if self.args.token:
            if not is_valid_token(tr, self.args.token):
                logger.critical("Token is invalid")
                return 10
            else:
                logger.info("Writing new token")
                write_token(self.args.token, self.args.workdir)
                return 0

        configured_token = read_token(self.args.workdir)

        if self.args.interactive:
            if is_valid_token(tr, configured_token):
                logger.warning("Trello access setup already completed. Current token will be overwritten")
            url = generate_token_url(tr)
            logger.info("Go to `%s`, authorize a token, and give it to me" % url)
            while True:
                token_candidate = raw_input("Token: ")
                if is_valid_token(tr, token_candidate):
                    write_token(token_candidate, self.args.workdir)
                    return 0
                else:
                    logger.error("Invalid token")

        if configured_token is None:
            logger.info("No Trello access token configured, yet")
            url = generate_token_url(tr)
            logger.info("Go to `%s` to authorize a new token and pass it with the `--token` argument" % url)
            return 1

        if is_valid_token(tr, configured_token):
            logger.warning("Trello access setup already completed")
            url = generate_token_url(tr)
            logger.info("If you need a new token, go to `%s` and pass it with the `--token` argument" % url)
            return 0

        else:
            logger.error("Trello access token is already configured, but invalid")
            url = generate_token_url(tr)
            logger.info("If you need a new token, go to `%s` and pass it with the `--token` argument" % url)
            return 5
