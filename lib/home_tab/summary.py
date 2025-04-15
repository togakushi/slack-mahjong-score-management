"""
lib/home_tab/summary.py
"""

import logging

import lib.global_value as g
from lib.command import graph, results
from lib.function import message, slack_api
from lib.home_tab import ui_parts
from lib.utils import dictutil


def build_summary_menu():
    """サマリメニュー生成"""
    g.app_var["screen"] = "SummaryMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    ui_parts.header("【成績サマリ】")

    # 検索範囲設定
    ui_parts.divider()
    ui_parts.radio_buttons(
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": "今月",
            "先月": "先月",
            "全部": "全部",
            "指定": f"範囲指定：{g.app_var['sday']} ～ {g.app_var['eday']}",
        },
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
    ui_parts.radio_buttons(
        id_suffix="output_option",
        title="出力オプション",
        flag={
            "normal": "通算ポイント",
            "score_comparisons": "通算ポイント比較",
            "point": "ポイント推移グラフ",
            "rank": "順位推移グラフ",
            "rating": "レーティング",
        },
    )

    ui_parts.divider()
    ui_parts.button(text="集計", action_id="summary_aggregation", style="primary")
    ui_parts.button(text="戻る", action_id="actionId-back", style="danger")


@g.app.action("summary_menu")
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
    logging.info("[summary_menu] %s", g.app_var)

    build_summary_menu()
    client.views_publish(
        user_id=g.app_var["user_id"],
        view=g.app_var["view"],
    )


@g.app.action("summary_aggregation")
def handle_aggregation_action(ack, body, client):
    """成績サマリ集計

    Args:
        ack (_type_): ack
        body (dict): イベント内容
        client (slack_bolt.App.client): slack_boltオブジェクト
    """

    ack()
    logging.trace(body)  # type: ignore
    g.msg.parser(body)
    g.msg.client = client

    argument, app_msg, update_flag = ui_parts.set_command_option(body)
    g.cfg.results.update(argument)
    g.cfg.results.update_from_dict(update_flag)
    g.params = dictutil.placeholder(g.cfg.results)

    client.views_update(
        view_id=g.app_var["view_id"],
        view=ui_parts.plain_text(f"{chr(10).join(app_msg)}"),
    )

    app_msg.pop()
    app_msg.append("集計完了")
    msg1 = ""
    msg2 = message.reply(message="no_hits")

    match g.app_var.get("operation"):
        case "point":
            count, ret = graph.summary.point_plot()
            if count:
                slack_api.post_fileupload("ポイント推移", ret)
            else:
                slack_api.post_message(ret)
        case "rank":
            count, ret = graph.summary.rank_plot()
            if count:
                slack_api.post_fileupload("順位変動", ret)
            else:
                slack_api.post_message(ret)
        case "rating":
            msg1, msg2, file_list = results.rating.aggregation()
            slack_api.slack_post(
                headline=msg1,
                message=msg2,
                summarize=False,
                file_list=file_list,
            )
        case _:
            msg1, msg2, file_list = results.summary.aggregation()
            slack_api.slack_post(
                headline=msg1,
                message=msg2,
                summarize=False,
                file_list=file_list,
            )

    client.views_update(
        view_id=g.app_var["view_id"],
        view=ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}".strip()),
    )


@g.app.view("SummaryMenu_ModalPeriodSelection")
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
        view=build_summary_menu(),
    )
