"""
libs/functions/tools/comparison.py
"""

import logging
import os

from slack_bolt import App
from slack_sdk import WebClient

import libs.global_value as g
from integrations import factory
from integrations.slack import comparison
from libs.functions import configuration


def main():
    """データ突合処理"""
    m = factory.select_parser("test")
    if g.args.compar:
        try:
            g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.appclient = g.app.client
            g.bot_id = g.app.client.auth_test()["user_id"]
            configuration.read_memberslist(False)
        except Exception as e:
            raise RuntimeError(e) from e

        count, _ = comparison.data_comparison(m)
        logging.notice(", ".join(f"{k}: {v}" for k, v in count.items()))  # type: ignore
