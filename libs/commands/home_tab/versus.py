"""
libs/commands/home_tab/versus.py
"""

import logging

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.commands import results
from libs.commands.home_tab import ui_parts
from libs.functions import slack_api
from libs.handler_registry import register
from libs.utils import dictutil


def build_versus_menu():
    """対戦結果メニュー生成"""
    g.app_var["screen"] = "VersusMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    ui_parts.header("【直接対戦】")

    # プレイヤー選択リスト
    ui_parts.user_select_pulldown(text="対象プレイヤー")
    ui_parts.multi_select_pulldown(text="対戦相手", add_list=["全員"])

    # 検索範囲設定
    [s1, e1] = ExtDt.get_range("今月")
    [s2, e2] = ExtDt.get_range("先月")
    [s3, e3] = ExtDt.get_range("全部")
    ui_parts.divider()
    ui_parts.radio_buttons(
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": f"今月：{s1.format("ymd")} ～ {e1.format("ymd")}",
            "先月": f"先月：{s2.format("ymd")} ～ {e2.format("ymd")}",
            "全部": f"全部：{s3.format("ymd")} ～ {e3.format("ymd")}",
            "指定": f"範囲指定：{g.app_var['sday']} ～ {g.app_var['eday']}",
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
    ui_parts.button(text="集計", action_id="versus_aggregation", style="primary")
    ui_parts.button(text="戻る", action_id="actionId-back", style="danger")


@register
def register_versus_handlers(app):
    """直接対戦メニュー"""
    @app.action("versus_menu")
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
        logging.info("[versus_menu] %s", g.app_var)

        build_versus_menu()
        client.views_publish(
            user_id=g.app_var["user_id"],
            view=g.app_var["view"],
        )

    @app.action("versus_aggregation")
    def handle_aggregation_action(ack, body, client):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        logging.trace(body)  # type: ignore
        g.msg.parser(body)
        g.msg.client = client

        g.msg.argument, app_msg, update_flag = ui_parts.set_command_option(body)
        g.cfg.results.update_from_dict(update_flag)
        g.params = dictutil.placeholder(g.cfg.results)

        search_options = body["view"]["state"]["values"]
        if "bid-user_select" in search_options:
            user_select = search_options["bid-user_select"]["player"]["selected_option"]
            if user_select is None:
                return
        if "bid-multi_select" in search_options:
            if len(search_options["bid-multi_select"]["player"]["selected_options"]) == 0:
                return

        client.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}")
        )

        app_msg.pop()
        app_msg.append("集計完了")

        msg1, msg2, file_list = results.versus.aggregation()
        slack_api.slack_post(
            headline=msg1,
            message=msg2,
            file_list=file_list,
        )

        client.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}"),
        )

    @app.view("VersusMenu_ModalPeriodSelection")
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
            view=build_versus_menu(),
        )
