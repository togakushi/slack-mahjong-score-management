"""
lib/home_tab/versus.py
"""

import logging

import lib.global_value as g
from lib import command as c
from lib import function as f
from lib import home_tab as h


def build_versus_menu():
    """対戦結果メニュー生成"""
    g.app_var["screen"] = "VersusMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    h.ui_parts.header("【直接対戦】")

    # プレイヤー選択リスト
    h.ui_parts.user_select(text="対象プレイヤー")
    h.ui_parts.multi_select(text="対戦相手", add_list=["全員"])

    h.ui_parts.divider()
    h.ui_parts.radio_buttons(
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": "今月",
            "先月": "先月",
            "全部": "全部",
            "指定": f"範囲指定：{g.app_var['sday']} ～ {g.app_var['eday']}",
        }
    )
    h.ui_parts.button(text="検索範囲設定", action_id="modal-open-period")

    # オプション
    h.ui_parts.divider()
    h.ui_parts.checkboxes(
        id_suffix="search_option",
        title="検索オプション",
        flag={
            "unregistered_replace": "ゲスト無効",
        },
        initial=["unregistered_replace"],
    )
    h.ui_parts.checkboxes(
        id_suffix="display_option",
        title="表示オプション",
        flag={
            "versus_matrix": "対戦結果",
            "game_results": "戦績（簡易）",
            "verbose": "戦績（詳細）",
        },
    )

    h.ui_parts.divider()
    h.ui_parts.button(text="集計", action_id="versus_aggregation", style="primary")
    h.ui_parts.button(text="戻る", action_id="actionId-back", style="danger")


@g.app.action("versus_menu")
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


@g.app.action("versus_aggregation")
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

    g.opt.initialization("results")
    argument, app_msg = h.home.set_command_option(body)
    g.opt.update(argument)
    g.prm.update(g.opt)

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
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}")
    )

    logging.info("[app:personal_aggregation] %s, %s", argument, vars(g.opt))

    app_msg.pop()
    app_msg.append("集計完了")

    msg1, msg2, file_list = c.results.versus.aggregation()
    f.slack_api.slack_post(
        headline=msg1,
        message=msg2,
        file_list=file_list,
    )

    client.views_update(
        view_id=g.app_var["view_id"],
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}"),
    )


@g.app.view("VersusMenu_ModalPeriodSelection")
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
