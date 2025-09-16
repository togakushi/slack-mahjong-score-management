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

import libs.event_dispatcher
import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from integrations.slack import config
from integrations.slack.events import comparison, slash
from integrations.slack.events.handler_registry import register, register_all
from integrations.slack.events.home_tab import home


def main():
    """メイン処理"""

    g.app_config = cast(config.AppConfig, g.app_config)

    # スラッシュコマンド登録
    g.slash_command_name = g.app_config.slash_command
    g.slash_commands = {"help": slash.command_help}

    # 個別コマンド登録
    g.special_commands = {
        g.app_config.comparison_word: comparison.main,
        f"Reminder: {g.app_config.comparison_word}": comparison.main,
        f"{g.app_config.slash_command} check": comparison.main,
    }
    g.special_commands.update({f"{g.app_config.slash_command} {x}": comparison.main for x in g.app_config.comparison_alias})

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

    m = factory.select_parser(g.selected_service)

    @app.event("message")
    def handle_message_events(body):
        """メッセージイベント

        Args:
            body (dict): ポストされたデータ
        """

        m.parser(body)
        libs.event_dispatcher.dispatch_by_keyword(m)

    @app.command(g.slash_command_name)
    def slash_command(ack, body):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
        """

        ack()
        m.parser(body)
        libs.event_dispatcher.dispatch_by_keyword(m)

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
