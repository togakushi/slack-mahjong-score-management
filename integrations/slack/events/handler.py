"""
integrations/slack/events/handler.py
"""

import logging
import os
import sys
from typing import cast

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import libs.dispatcher
import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.slack.adapter import AdapterInterface
from integrations.slack.events.handler_registry import register, register_all
from integrations.slack.events.home_tab import home


def main(adapter: AdapterInterface):
    """メイン処理"""

    try:
        app = App(token=os.environ["SLACK_BOT_TOKEN"])
        adapter.conf.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        adapter.conf.appclient = app.client
        register_all(app)  # イベント遅延登録
    except SlackApiError as err:
        logging.error(err)
        sys.exit()

    adapter.conf.bot_id = app.client.auth_test()["user_id"]
    g.adapter = adapter

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()


@register
def register_event_handlers(app):
    """イベントAPI"""

    adapter = cast(AdapterInterface, g.adapter)
    m = adapter.parser()

    @app.event("message")
    def handle_message_events(body):
        """メッセージイベント

        Args:
            body (dict): ポストされたデータ
        """

        m.reset()
        m.parser(body)
        libs.dispatcher.by_keyword(m)

    @app.command(adapter.conf.slash_command)
    def slash_command(ack, body):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
        """

        ack()
        m.reset()
        m.parser(body)
        libs.dispatcher.by_keyword(m)

    @app.event("app_home_opened")
    def handle_home_events(event):
        """ホームタブオープン

        Args:
            event (dict): イベント内容
        """

        adapter.conf.tab_var = {
            "view": {},
            "no": 0,
            "user_id": None,
            "view_id": None,
            "screen": None,
            "operation": None,
            "sday": adapter.conf.tab_var.get("sday", ExtDt().format("ymd", "-")),
            "eday": adapter.conf.tab_var.get("eday", ExtDt().format("ymd", "-")),
        }

        adapter.conf.tab_var["user_id"] = event["user"]
        if "view" in event:
            adapter.conf.tab_var["view_id"] = event["view"]["id"]

        logging.trace(adapter.conf.tab_var)  # type: ignore

        home.build_main_menu()
        result = adapter.conf.appclient.views_publish(
            user_id=adapter.conf.tab_var["user_id"],
            view=adapter.conf.tab_var["view"],
        )
        logging.trace(result)  # type: ignore
