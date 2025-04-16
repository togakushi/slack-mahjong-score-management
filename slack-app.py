#!/usr/bin/env python3
"""slack-app.py

Slackに投稿された麻雀のスコアを記録し、集計して表示するツール
"""

import logging
import os
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import libs.global_value as g
from libs.data import initialization
from libs.functions import configuration
from libs.handler_registry import register_all

if __name__ == "__main__":
    g.script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        configuration.setup()
        app = App(token=os.environ["SLACK_BOT_TOKEN"])
        g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        from libs import event
        __all__ = ["event"]
        register_all(app)  # イベント遅延登録
    except SlackApiError as err:
        logging.error(err)
        sys.exit()

    initialization.initialization_resultdb()
    configuration.read_memberslist()
    g.app = app  # インスタンスグローバル化
    g.bot_id = app.client.auth_test()["user_id"]

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
