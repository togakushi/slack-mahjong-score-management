import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


def build_personal_menu():
    g.app_var["screen"] = "PersonalMenu"
    no = 0
    flag = ["unregistered_replace", "versus_matrix", "game_results", "verbose"]
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【個人成績】")

    # プレイヤー選択リスト
    view, no = e.UserSelect(view, no, text = "対象プレイヤー")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(view, no, text = "検索範囲設定", value = "click_versus", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, flag)
    view, no = e.DisplayOptions(view, no, flag)

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "click_personal", action_id = "search_personal", style = "primary")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back", style = "danger")

    return(view)


@g.app.action("menu_personal")
def handle_menu_action(ack, body, client):
    ack()
    g.logging.trace(body) # type: ignore

    g.app_var["user_id"] = body["user"]["id"]
    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[menu_personal] {g.app_var}")

    client.views_publish(
        user_id = g.app_var["user_id"],
        view = build_personal_menu(),
    )


@g.app.action("search_personal")
def handle_search_action(ack, body, client):
    ack()
    g.logging.trace(body) # type: ignore

    argument, command_option, app_msg = e.set_command_option(
        f.configure.command_option_initialization("results"),
        body,
    )
    params, _ = f.common.game_info(argument, command_option)

    search_options = body["view"]["state"]["values"]
    if "bid-user_select" in search_options:
        user_select = search_options["bid-user_select"]["player"]["selected_option"]
        if user_select == None:
            return

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}")
    )

    g.logging.info(f"[app:search_personal] {argument}, {command_option}")

    app_msg.pop()
    app_msg.append("集計完了")
    msg1 = f.message.no_hits(params)

    msg1, msg2 = c.results.personal.aggregation(argument, command_option)
    res = f.slack_api.post_message(client, body["user"]["id"], msg1)
    for m in msg2.keys():
        f.slack_api.post_message(client, body["user"]["id"], msg2[m] + "\n", res["ts"])

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{chr(10).join(app_msg)}\n\n{msg1}"),
    )


@g.app.view("PersonalMenu_ModalPeriodSelection")
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
        view = build_personal_menu(),
    )
