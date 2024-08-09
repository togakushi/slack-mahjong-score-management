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
def handle_menu_action(ack, body, client):
    ack()
    g.logging.trace(body) # type: ignore

    g.app_var["user_id"] = body["user"]["id"]
    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[menu_summary] {g.app_var}")

    client.views_publish(
        user_id = g.app_var["user_id"],
        view = build_summary_enu(),
    )


@g.app.action("search_summary")
def handle_search_action(ack, body, client):
    ack()
    g.logging.trace(body) # type: ignore

    g.opt.initialization("results")
    argument, app_msg = e.set_command_option(body)
    g.opt.update(argument)
    g.prm.update(g.opt)

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}"),
    )

    g.logging.info(f"[app:search_summary] {argument}, {vars(g.opt)}")

    app_msg.pop()
    app_msg.append("集計完了")
    msg2 = f.message.no_hits()

    msg1, msg2, file_list = c.results.summary.aggregation()
    f.slack_api.slack_post(
        client = client,
        channel = body["user"]["id"],
        headline = msg1,
        message = msg2,
        summarize = False,
        file_list =file_list,
    )

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}\n\n{msg1}"),
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
