"""
libs/commands/home_tab/personal.py
"""

import logging

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from libs.commands import results
from libs.commands.home_tab import ui_parts
from libs.functions import message
from libs.functions.events.handler_registry import register
from libs.utils import dictutil


def build_personal_menu():
    """個人成績メニュー作成"""
    g.app_var["screen"] = "PersonalMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    ui_parts.header(text="【個人成績】")

    # プレイヤー選択リスト
    ui_parts.user_select_pulldown(text="対象プレイヤー")

    # 検索範囲設定
    date_dict = {x: ExtDt(hours=-g.cfg.setting.time_adjust).range(x).dict_format("ymd", "-") for x in ["今月", "先月", "全部"]}
    ui_parts.divider()
    ui_parts.radio_buttons(
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": f"今月：{date_dict["今月"]["start"]} ～ {date_dict["今月"]["end"]}",
            "先月": f"先月：{date_dict["先月"]["start"]} ～ {date_dict["先月"]["end"]}",
            "全部": f"全部：{date_dict["全部"]["start"]} ～ {date_dict["全部"]["end"]}",
            "指定": f"範囲指定：{g.app_var["sday"]} ～ {g.app_var["eday"]}",
        }
    )
    ui_parts.button(text="検索範囲設定", action_id="modal-open-period")

    # オプション
    ui_parts.divider()
    ui_parts.checkboxes(
        id_suffix="search_option",
        title="検索オプション",
        flag={
            "unregistered_replace": "ゲスト無効",
        },
        initial=["unregistered_replace"],
    )
    ui_parts.checkboxes(
        id_suffix="display_option",
        title="表示オプション",
        flag={
            "versus_matrix": "対戦結果",
            "game_results": "戦績（簡易）",
            "verbose": "戦績（詳細）",
        },
    )

    ui_parts.divider()
    ui_parts.button(text="集計", action_id="personal_aggregation", style="primary")
    ui_parts.button(text="戻る", action_id="actionId-back", style="danger")


@register
def register_personal_handlers(app):
    """個人成績メニュー"""
    @app.action("personal_menu")
    def handle_menu_action(ack, body, client):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        logging.trace(body)  # type: ignore

        g.app_var["user_id"] = body["user"]["id"]
        g.app_var["view_id"] = body["view"]["id"]
        logging.info("[personal_menu] %s", g.app_var)

        build_personal_menu()
        client.views_publish(
            user_id=g.app_var["user_id"],
            view=g.app_var["view"],
        )

    @app.action("personal_aggregation")
    def handle_aggregation_action(ack, body, client):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        logging.trace(body)  # type: ignore

        api_adapter = factory.select_adapter(g.selected_service)

        g.msg.parser(body)
        g.msg.client = client

        g.msg.argument, app_msg, update_flag = ui_parts.set_command_option(body)
        g.params = dictutil.placeholder(g.cfg.results)
        g.params.update(update_flag)

        search_options = body["view"]["state"]["values"]
        if "bid-user_select" in search_options:
            user_select = search_options["bid-user_select"]["player"]["selected_option"]
            if user_select is None:
                return

        client.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}")
        )

        app_msg.pop()
        app_msg.append("集計完了")
        msg1 = message.random_reply(message="no_hits")

        msg1, msg2 = results.detail.aggregation()
        res = api_adapter.post_message(msg1)
        for _, val in msg2.items():
            api_adapter.post_message(str(val + "\n"), res["ts"])

        client.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}"),
        )

    @app.view("PersonalMenu_ModalPeriodSelection")
    def handle_view_submission(ack, view, client):
        """view更新

        Args:
            ack (_type_): ack
            view (dict): 描写内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        for i in view["state"]["values"].keys():
            if "aid-sday" in view["state"]["values"][i]:
                g.app_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
            if "aid-eday" in view["state"]["values"][i]:
                g.app_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

        logging.info("[global var] %s", g.app_var)

        client.views_update(
            view_id=g.app_var["view_id"],
            view=build_personal_menu(),
        )
