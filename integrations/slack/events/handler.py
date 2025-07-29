"""
integrations/slack/events/handler.py
"""

import logging
import os
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import libs.global_value as g
from integrations.slack.events import message_event, slash_event, tab_event
from integrations.slack.events.handler_registry import register, register_all


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

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()


@register
def register_event_handlers(app):
    """イベントAPI"""
    @app.event("message")
    def handle_message_events(body):
        """ポストされた内容で処理を分岐

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            body (dict): ポストされたデータ
        """
        message_event.main(body)

    @app.command(g.cfg.setting.slash_command)
    def slash_command(ack, body):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
            client (slack_bolt.App.client): slack_boltオブジェクト
        """
        slash_event.main(ack, body)

    @app.event("app_home_opened")
    def handle_home_events(event):
        """ホームタブオープン

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            event (dict): イベント内容
        """
        tab_event.main(event)
