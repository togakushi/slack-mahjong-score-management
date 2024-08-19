import lib.command as c
import lib.event as e
import lib.function as f
from lib.function import global_value as g


def build_versus_menu():
    g.app_var["screen"] = "VersusMenu"
    no = 0
    flag = ["unregistered_replace", "game_results", "verbose"]
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【直接対戦】")

    # プレイヤー選択リスト
    view, no = e.UserSelect(view, no, text="対象プレイヤー")
    view, no = e.MultiSelect(view, no, text="対戦相手", add_list=["全員"])

    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(
        view, no,
        text="検索範囲設定",
        value="click_versus",
        action_id="modal-open-period"
    )

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, flag)
    view, no = e.DisplayOptions(view, no, flag)

    view, no = e.Divider(view, no)
    view, no = e.Button(
        view, no,
        text="集計開始",
        value="click_versus",
        action_id="search_versus",
        style="primary"
    )
    view, no = e.Button(
        view, no,
        text="戻る",
        value="click_back",
        action_id="actionId-back",
        style="danger"
    )

    return (view)


@g.app.action("menu_versus")
def handle_menu_action(ack, body, client):
    ack()
    g.logging.trace(body)  # type: ignore

    g.app_var["user_id"] = body["user"]["id"]
    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[menu_versus] {g.app_var}")

    client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_versus_menu(),
    )


@g.app.action("search_versus")
def handle_search_action(ack, body, client):
    ack()
    g.logging.trace(body)  # type: ignore
    g.msg.parser(body)
    g.msg.client = client

    g.opt.initialization("results")
    argument, app_msg = e.set_command_option(body)
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
        view=e.PlainText(f"{chr(10).join(app_msg)}")
    )

    g.logging.info(f"[app:search_personal] {argument}, {vars(g.opt)}")

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
        view=e.PlainText(f"{chr(10).join(app_msg)}\n\n{msg1}"),
    )


@g.app.view("VersusMenu_ModalPeriodSelection")
def handle_view_submission(ack, view, client):
    ack()

    for i in view["state"]["values"].keys():
        if "aid-sday" in view["state"]["values"][i]:
            g.app_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
        if "aid-eday" in view["state"]["values"][i]:
            g.app_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

    g.logging.info(f"[global var] {g.app_var}")

    client.views_update(
        view_id=g.app_var["view_id"],
        view=build_versus_menu(),
    )
