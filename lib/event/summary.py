import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


def BuildSummryMenu():
    g.app_var["screen"] = "SummryMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【成績サマリ】")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no, block_id = "bid-range")
    view, no = e.Button(view, no, text = "検索範囲設定", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, block_id = "bid-option")

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "search", action_id = "search_summary")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")
    #view, no = e.Button(view, no, text = "てすと", action_id = "debug")

    return(view)


@g.app.action("menu_summary")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    g.logging.info(f"[menu_summary] {g.app_var}")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = BuildSummryMenu(),
    )


@g.app.action("search_summary")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    command_option, app_msg = e.SetCommandOption(
        f.configure.command_option_initialization("results"),
        body,
    )

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{app_msg}"),
    )

    target_days, target_player, target_count, command_option = f.common.argument_analysis("", command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    if starttime and endtime:
        msg = c.results.summary(starttime, endtime, target_player, target_count, command_option)
        f.slack_api.post_text(client, body["user"]["id"], False, "", msg)

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{app_msg}\n集計完了"),
    )


@g.app.view("SummryMenu_ModalPeriodSelection")
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
        view = BuildSummryMenu(),
    )
