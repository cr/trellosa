# -*- coding: utf8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os


logger = logging.getLogger(__name__)


class TagsDB(object):
    """
    Class to manage snapshot tags
    """

    def __init__(self, args):
        self.args = args
        self.tags_file = os.path.abspath(os.path.join(args.workdir, "tags.json"))
        try:
            with open(self.tags_file, "r") as f:
                self.tags = json.load(f)
        except IOError:
            self.tags = dict()

    @staticmethod
    def is_valid_tag(tag):
        return type(tag) is str and tag.isalnum() and not tag.isdigit() and " " not in tag

    def tag_to_handle(self, tag):
        """
        Converts a tag to its associated handle
        :param tag: str with tag
        :return: str with tag or None
        """
        try:
            return self.tags[tag]
        except KeyError:
            return None

    def handle_to_tags(self, handle):
        """
        Converts a handle to its associated tags
        :param handle: str with handle
        :return: list of str with tags
        """
        tags = []
        for tag in self.tags:
            if self.tags[tag] == handle:
                tags.append(tag)
        return tags

    def exists(self, tag):
        """
        Check whether a tag exists
        :param tag: str with tag
        :return: bool
        """
        return tag in self.tags

    def list(self):
        """
        Returns a list of tags
        :return: list of str of tags
        """
        return sorted(self.tags.keys())

    def delete(self, tag, save=True):
        """
        Delete a tag
        :param tag: str with tag
        :return: None
        """
        if tag in self.tags:
            del self.tags[tag]
        else:
            logger.warning("Tag `%s` does not exist")
        if save:
            self.save()

    def add(self, tag, handle, save=True):
        """
        Add tag, overwriting existing tag
        :param tag: str with tag
        :param handle: str with handle
        :return: None
        """
        self.tags[tag] = handle
        if save:
            self.save()

    def save(self):
        with open(self.tags_file, "w") as f:
            json.dump(self.tags, f, indent=4, sort_keys=True)
