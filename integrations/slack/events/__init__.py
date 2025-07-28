"""
イベント処理

Exports:
- `integrations.slack.events.handler_registry`: イベント遅延登録
- `integrations.slack.events.handler`: イベントハンドラ
- `integrations.slack.events.message_event`: メッセージイベントリスナ
- `integrations.slack.events.slash_event`: スラッシュコマンドイベントリスナ
- `integrations.slack.events.tab_event`: ホームタブイベントリスナ
"""

import logging
import os
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import libs.global_value as g
from integrations.slack.events.handler_registry import register_all


def main():
    """メイン処理"""
    try:
        app = App(token=os.environ["SLACK_BOT_TOKEN"])
        g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        g.appclient = app.client
        register_all(app)  # イベント遅延登録
    except SlackApiError as err:
        logging.error(err)
        sys.exit()

    g.app = app  # インスタンスグローバル化
    g.bot_id = app.client.auth_test()["user_id"]

    sm_handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    sm_handler.start()
