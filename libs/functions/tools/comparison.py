"""
lib/function/tools/comparison.py
"""

import logging
import os

from slack_bolt import App
from slack_sdk import WebClient

import libs.global_value as g
from libs.data import comparison
from libs.functions import configuration


def main():
    """データ突合処理"""
    if g.args.compar:
        try:
            g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.bot_id = g.app.client.auth_test()["user_id"]
            configuration.read_memberslist(False)
        except Exception as e:
            raise RuntimeError(e) from e

        count, _ = comparison.data_comparison()
        logging.notice(", ".join(f"{k}: {v}" for k, v in count.items()))  # type: ignore
