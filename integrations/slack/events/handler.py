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

import libs.event_dispatcher
import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from integrations.slack.events import slash_event
from integrations.slack.events.handler_registry import register, register_all
from libs.commands.home_tab import home


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
            body (dict): ポストされたデータ
        """

        logging.trace(body)  # type: ignore
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(body)

        # キーワード処理
        libs.event_dispatcher.dispatch_by_keyword(m)

    @app.command(g.cfg.setting.slash_command)
    def slash_command(ack, body):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
        """
        slash_event.main(ack, body)

    @app.event("app_home_opened")
    def handle_home_events(event):
        """ホームタブオープン

        Args:
            event (dict): イベント内容
        """

        g.app_var = {
            "view": {},
            "no": 0,
            "user_id": None,
            "view_id": None,
            "screen": None,
            "operation": None,
            "sday": g.app_var.get("sday", ExtDt().format("ymd", "-")),
            "eday": g.app_var.get("eday", ExtDt().format("ymd", "-")),
        }

        g.app_var["user_id"] = event["user"]
        if "view" in event:
            g.app_var["view_id"] = event["view"]["id"]

        logging.trace(g.app_var)  # type: ignore

        home.build_main_menu()
        result = g.appclient.views_publish(
            user_id=g.app_var["user_id"],
            view=g.app_var["view"],
        )
        logging.trace(result)  # type: ignore
