import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


def BuildRankingMenu():
    g.app_var["screen"] = "RankingMenu"
    no = 0
    flag = ["unregistered_replace", "archive"]
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【ランキング】")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(view, no, text = "検索範囲設定", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, flag)

    view, no = e.InputRanked(view, no, block_id = "bid-ranked")

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "click_personal", action_id = "search_ranking", style = "primary")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back", style = "danger")

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

    argument, command_option, app_msg = e.SetCommandOption(
        f.configure.command_option_initialization("ranking"),
        body,
    )

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}"),
    )

    search_options = body["view"]["state"]["values"]
    if "bid-ranked" in search_options:
        if "value" in search_options["bid-ranked"]["aid-ranked"]:
            ranked = int(search_options["bid-ranked"]["aid-ranked"]["value"])
            if ranked > 0:
                argument.append(f"トップ{ranked}")

    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    if starttime and endtime:
        msg1, msg2 = c.ranking.getdata(starttime, endtime, target_player, target_count, command_option)
        res = f.slack_api.post_message(client, body["user"]["id"], msg1)
        if msg2:
            f.slack_api.post_message(client, body["user"]["id"], msg2, res["ts"])

    app_msg.pop()
    app_msg.append("集計完了")
    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}\n\n{msg1}"),
    )


@g.app.view("RankingMenu_ModalPeriodSelection")
def handle_view_submission(ack, view, client):
    ack()

    for i in view["state"]["values"].keys():
        if "aid-sday" in view["state"]["values"][i]:
            g.app_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
        if "aid-eday" in view["state"]["values"][i]:
            g.app_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

    client.views_update(
        view_id = g.app_var["view_id"],
        view = BuildRankingMenu(),
    )
