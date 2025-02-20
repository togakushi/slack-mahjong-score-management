import logging

import lib.global_value as g
from lib import command as c
from lib import function as f
from lib import home_tab as h


def build_personal_menu():
    """個人成績メニュー作成

    Returns:
        dict: viewに描写する内容
    """

    g.app_var["screen"] = "PersonalMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = h.ui_parts.header(view, no, "【個人成績】")

    # プレイヤー選択リスト
    view, no = h.ui_parts.user_select(view, no, text="対象プレイヤー")

    # 検索範囲設定
    view, no = h.ui_parts.divider(view, no)
    view, no = h.ui_parts.radio_buttons(
        view, no, "search_range", "検索範囲",
        {
            "今月": "今月",
            "先月": "先月",
            "全部": "全部",
            "指定": f"範囲指定：{g.app_var['sday']} ～ {g.app_var['eday']}",
        }
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
    view, no = h.ui_parts.checkboxes(
        view, no, "display_option", "表示オプション",
        {
            "versus_matrix": "対戦結果",
            "game_results": "戦績（簡易）",
            "verbose": "戦績（詳細）",
        },
    )

    view, no = h.ui_parts.divider(view, no)
    view, no = h.ui_parts.button(view, no, text="集計", action_id="personal_aggregation", style="primary")
    view, no = h.ui_parts.button(view, no, text="戻る", action_id="actionId-back", style="danger")

    return (view)


@g.app.action("personal_menu")
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
    logging.info(f"[personal_menu] {g.app_var}")

    client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_personal_menu(),
    )


@g.app.action("personal_aggregation")
def handle_aggregation_action(ack, body, client):
    """メニュー項目生成

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

    search_options = body["view"]["state"]["values"]
    if "bid-user_select" in search_options:
        user_select = search_options["bid-user_select"]["player"]["selected_option"]
        if user_select is None:
            return

    client.views_update(
        view_id=g.app_var["view_id"],
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}")
    )

    logging.info(f"[app:personal_aggregation] {argument}, {vars(g.opt)}")

    app_msg.pop()
    app_msg.append("集計完了")
    msg1 = f.message.reply(message="no_hits")

    msg1, msg2 = c.results.detail.aggregation()
    res = f.slack_api.post_message(msg1)
    for m in msg2.keys():
        f.slack_api.post_message(msg2[m] + "\n", res["ts"])

    client.views_update(
        view_id=g.app_var["view_id"],
        view=h.ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}"),
    )


@g.app.view("PersonalMenu_ModalPeriodSelection")
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

    logging.info(f"[global var] {g.app_var}")

    client.views_update(
        view_id=g.app_var["view_id"],
        view=build_personal_menu(),
    )
