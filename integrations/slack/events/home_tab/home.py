"""
integrations/slack/events/home_tab/home.py
"""

import logging
from typing import cast

import libs.global_value as g
from integrations.slack import config
from integrations.slack.events.handler_registry import register
from integrations.slack.events.home_tab import ui_parts


def build_main_menu():
    """メインメニューを生成する"""
    g.app_config.tab_var["screen"] = "MainMenu"
    g.app_config.tab_var["no"] = 0
    g.app_config.tab_var["view"] = {"type": "home", "blocks": []}
    ui_parts.button(text="成績サマリ", action_id="summary_menu")
    ui_parts.button(text="ランキング", action_id="ranking_menu")
    ui_parts.button(text="個人成績", action_id="personal_menu")
    ui_parts.button(text="直接対戦", action_id="versus_menu")


@register
def register_home_handlers(app):
    """ホームタブ操作イベント"""
    @app.action("actionId-back")
    def handle_action(ack, body):
        """戻るボタン

        Args:
            ack (_type_): ack
            body (dict): イベント内容
        """

        ack()
        logging.trace(body)  # type: ignore

        g.app_config = cast(config.AppConfig, g.app_config)

        build_main_menu()
        g.app_config.appclient.views_publish(
            user_id=g.app_config.tab_var["user_id"],
            view=g.app_config.tab_var["view"],
        )

    @app.action("modal-open-period")
    def handle_open_modal_button_clicks(ack, body):
        """検索範囲設定選択イベント

        Args:
            ack (_type_): ack
            body (dict): イベント内容
            client (slack_bolt.App.client): オブジェクト
        """

        ack()

        g.app_config = cast(config.AppConfig, g.app_config)

        g.app_config.appclient.views_open(
            trigger_id=body["trigger_id"],
            view=ui_parts.modalperiod_selection(),
        )
