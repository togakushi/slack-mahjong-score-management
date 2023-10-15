import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


def BuildRankingMenu():
    g.app_var["screen"] = "RankingMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【ランキング】")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no, block_id = "bid-range")
    view, no = e.Button(view, no, text = "検索範囲設定", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, block_id = "bid-option")

    view, no = e.InputRanked(view, no, block_id = "bid-ranked")

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "search", action_id = "search_ranking")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")
    #view, no = e.Button(view, no, text = "てすと", action_id = "debug")

    return(view)


@g.app.action("menu_ranking")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[menu_ranking] {g.app_var}")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = BuildRankingMenu(),
    )


@g.app.action("search_ranking")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    command_option, app_msg = e.SetCommandOption(
        f.configure.command_option_initialization("ranking"),
        body,
    )

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{app_msg}"),
    )

    target_days, target_player, target_count, command_option = f.common.argument_analysis("", command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    if starttime and endtime:
        msg1, msg2 = c.ranking.getdata(starttime, endtime, target_player, target_count, command_option)
        res = f.slack_api.post_message(client, body["user"]["id"], msg1)
        if msg2:
            f.slack_api.post_message(client, body["user"]["id"], msg2, res["ts"])

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{app_msg}\n集計完了\n\n{msg1}"),
    )


@g.app.view("RankingMenu_ModalPeriodSelection")
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
        view = BuildRankingMenu(),
    )
