"""
libs/commands/home_tab/home.py
"""

import logging

import libs.global_value as g
from libs.commands.home_tab import ui_parts
from integrations.slack.events.handler_registry import register


def build_main_menu():
    """メインメニューを生成する"""
    g.app_var["screen"] = "MainMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
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

        build_main_menu()
        g.appclient.views_publish(
            user_id=g.app_var["user_id"],
            view=g.app_var["view"],
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
        g.appclient.views_open(
            trigger_id=body["trigger_id"],
            view=ui_parts.modalperiod_selection(),
        )
