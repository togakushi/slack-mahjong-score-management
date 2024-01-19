import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


def build_summary_enu():
    g.app_var["screen"] = "SummaryMenu"
    no = 0
    flag = ["unregistered_replace", "score_comparisons"]
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【成績サマリ】")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(view, no, text = "検索範囲設定", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, flag)
    view, no = e.DisplayOptions(view, no, flag)

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "click_summary", action_id = "search_summary", style = "primary")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back", style = "danger")

    return(view)


@g.app.action("menu_summary")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    g.app_var["user_id"] = body["user"]["id"]
    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[menu_summary] {g.app_var}")

    client.views_publish(
        user_id = g.app_var["user_id"],
        view = build_summary_enu(),
    )


@g.app.action("search_summary")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    argument, command_option, app_msg = e.set_command_option(
        f.configure.command_option_initialization("results"),
        body,
    )

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}"),
    )

    g.logging.info(f"[app:search_summary] {argument}, {command_option}")

    app_msg.pop()
    app_msg.append("集計完了")
    msg2 = f.message.no_hits(argument, command_option)

    msg1, msg2, msg3 = c.results.summary.aggregation(argument, command_option)
    if msg1:
        res = f.slack_api.post_message(client, body["user"]["id"], msg2)
        f.slack_api.post_text(client, body["user"]["id"], res["ts"], "", msg1)
    if msg3:
        f.slack_api.post_message(client, body["user"]["id"], msg3, res["ts"])

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}\n\n{msg2}"),
    )


@g.app.view("SummaryMenu_ModalPeriodSelection")
def handle_view_submission(ack, view, client):
    ack()

    for i in view["state"]["values"].keys():
        if "aid-sday" in view["state"]["values"][i]:
            g.app_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
        if "aid-eday" in view["state"]["values"][i]:
            g.app_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

    g.logging.info(f"[global var] {g.app_var}")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = build_summary_enu(),
    )
