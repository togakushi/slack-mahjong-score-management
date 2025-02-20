import logging

import lib.global_value as g
from lib import command as c
from lib import function as f
from lib import home_tab as h


def build_summary_menu():
    """サマリメニュー生成

    Returns:
        dict: viewに描写する内容
    """

    g.app_var["screen"] = "SummaryMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = h.ui_parts.header(view, no, "【成績サマリ】")

    # 検索範囲設定
    view, no = h.ui_parts.divider(view, no)
    view, no = h.ui_parts.radio_buttons(
        view, no, "search_range", "検索範囲",
        {
            "今月": "今月",
            "先月": "先月",
            "全部": "全部",
            "指定": f"範囲指定：{g.app_var['sday']} ～ {g.app_var['eday']}",
        },
    )
    view, no = h.ui_parts.button(view, no, text="検索範囲設定", action_id="modal-open-period")

    # オプション
    view, no = h.ui_parts.divider(view, no)
    view, no = h.ui_parts.checkboxes(
        view, no, "search_option", "検索オプション",
        {
            "unregistered_replace": "ゲスト無効",
        },
        ["unregistered_replace"],
    )
    view, no = h.ui_parts.radio_buttons(
        view, no, "output_option", "出力オプション",
        {
            "normal": "通算ポイント",
            "score_comparisons": "通算ポイント比較",
            "point": "ポイント推移グラフ",
            "rank": "順位推移グラフ",
            "rating": "レーティング",
        },
    )

    view, no = h.ui_parts.divider(view, no)
    view, no = h.ui_parts.button(view, no, text="集計", action_id="summary_aggregation", style="primary")
    view, no = h.ui_parts.button(view, no, text="戻る", action_id="actionId-back", style="danger")

    return (view)


@g.app.action("summary_menu")
def handle_menu_action(ack, body, client):
    """メニュー項目生成

    Args:
        ack (_type_): ack
        body (dict): イベント内容
        client (slack_bolt.App.client): slack_boltオブジェクト
    """

    ack()
    logging.trace(body)

    g.app_var["user_id"] = body["user"]["id"]
    g.app_var["view_id"] = body["view"]["id"]
    logging.info("[summary_menu] %s", g.app_var)

    client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_summary_menu(),
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
    logging.trace(body)
    g.msg.parser(body)
    g.msg.client = client

    g.opt.initialization("results")
    argument, app_msg = h.home.set_command_option(body)
    g.opt.update(argument)
    g.prm.update(g.opt)

    client.views_update(
        view_id=g.app_var["view_id"],
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}"),
    )

    logging.info("[app:summary_aggregation] %s, %s", argument, vars(g.opt))

    app_msg.pop()
    app_msg.append("集計完了")
    msg1 = ""
    msg2 = f.message.reply(message="no_hits")

    match g.app_var.get("operation"):
        case "point":
            count, ret = c.graph.summary.point_plot()
            if count:
                f.slack_api.post_fileupload("ポイント推移", ret)
            else:
                f.slack_api.post_message(ret)
        case "rank":
            count, ret = c.graph.summary.rank_plot()
            if count:
                f.slack_api.post_fileupload("順位変動", ret)
            else:
                f.slack_api.post_message(ret)
        case "rating":
            msg1, msg2, file_list = c.results.rating.aggregation()
            f.slack_api.slack_post(
                headline=msg1,
                message=msg2,
                summarize=False,
                file_list=file_list,
            )
        case _:
            msg1, msg2, file_list = c.results.summary.aggregation()
            f.slack_api.slack_post(
                headline=msg1,
                message=msg2,
                summarize=False,
                file_list=file_list,
            )

    client.views_update(
        view_id=g.app_var["view_id"],
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}".strip()),
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
