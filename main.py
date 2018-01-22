#!/usr/bin/env python2
# -*- coding: utf8 -*-

import json
import os
import sys
from trello import TrelloApi

TRELLO_PUBLIC_APP_KEY = "fee6885be0783a3f421d5998840da9cb"



def get_token(tr, file_name):
    user_token = None

    if not os.path.exists(file_name):
        url = tr.get_token_url("TrelloSA", expires="never", write_access=False)
        user_token = raw_input("Go to `%s`, authorize a token, and give it to me: " % url)
        if len(user_token) != 64 or not user_token.isalnum():
            raise Exception("That does not look like a token at all.")
        with open(file_name, "w") as f:
            f.write(user_token)

    with open(file_name, "r") as f:
        user_token = f.readline().strip()

    os.chmod(file_name, 0600)

    if user_token is None or not user_token.isalnum() or len(user_token) != 64:
        raise Exception("What's wrong with your token? You need to either edit or delete `app_token.txt`.")

    return user_token


def main(argv):
    tr = TrelloApi(TRELLO_PUBLIC_APP_KEY)

    try:
        user_token = get_token(tr, "token.txt")

    except Exception as e:
        print e
        sys.exit(5)

    tr.set_token(user_token)

    board_id = "5887b9767bc90fd832e669f8"  # The Firefox board
    board = tr.boards.get(board_id)

    old_cards = dict()
    old_lists = dict()

    if os.path.exists("state.json"):
        with open("state.json", "r") as f:
            state = json.load(f)
            old_cards = state["cards"]
            old_lists = state["lists"]

    cards = dict(map(lambda x: [x["id"], x], tr.boards.get_card(board_id)))
    lists = dict(map(lambda x: [x["id"], x], map(tr.lists.get, set(map(lambda c: c["idList"], cards.itervalues())))))

    old_card_ids = set(old_cards.keys())
    old_list_ids = set(old_lists.keys())

    card_ids = set(cards.keys())
    list_ids = set(lists.keys())

    dropped_card_ids = old_card_ids - card_ids
    new_card_ids = card_ids - old_card_ids

    dropped_list_ids = old_list_ids - list_ids
    new_list_ids = list_ids - old_list_ids

    if len(new_card_ids) > 0 or len(dropped_card_ids) > 0 or len(dropped_list_ids) > 0 or len(new_list_ids) > 0:
        print "Something changed!"
        from IPython import embed
        embed()
    else:
        print "Same old"

    with open("state.json", "w") as f:
        json.dump({"cards": cards, "lists": lists}, f)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
