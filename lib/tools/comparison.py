import logging
import os
import sys

from slack_bolt import App
from slack_sdk import WebClient

import lib.global_value as g
from lib import command as c
from lib import database as d


def main():
    """データ突合処理
    """

    if g.args.compar:
        try:
            g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.bot_id = g.app.client.auth_test()["user_id"]
            c.member.read_memberslist(False)
        except Exception as e:
            sys.exit(f"Error: {e}")

        count, _ = d.comparison.data_comparison()
        logging.notice(", ".join(f"{k}: {v}" for k, v in count.items()))  # type: ignore
