#!/usr/bin/env python3
# pylint: disable=invalid-name
"""
slack-app.py - Slackに投稿された麻雀のスコアを記録し、集計して表示するツール

help:

    $ ./slack-app.py --help
    usage: slack-app.py [-h] [--debug] [--verbose] [--moderate] [--notime] [-c CONFIG]

    options:
    -h, --help            show this help message and exit
    --debug, --trace      デバッグ情報表示
    --verbose             詳細デバッグ情報表示
    --moderate            ログレベルがエラー以下のもを非表示
    --notime              ログフォーマットから日時を削除
    -c CONFIG, --config CONFIG
                            設定ファイル(default: config.ini)
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
from libs.functions.events.handler_registry import register_all

if __name__ == "__main__":
    try:
        configuration.setup()
        app = App(token=os.environ["SLACK_BOT_TOKEN"])
        g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        g.appclient = app.client
        from libs import event
        __all__ = ["event"]
        register_all(app)  # イベント遅延登録
    except SlackApiError as err:
        logging.error(err)
        sys.exit()

    initialization.initialization_resultdb()
    initialization.read_grade_table()
    configuration.read_memberslist()
    g.app = app  # インスタンスグローバル化
    g.bot_id = app.client.auth_test()["user_id"]

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
