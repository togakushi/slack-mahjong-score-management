import lib.event as e
from lib.function import global_value as g


def BuildVersusMenu():
    g.app_var["screen"] = "VersusMenu"
    no = 0
    view = {"type": "home", "blocks": []}

    view, no = e.Header(view, no, "【直接対戦】")
    # プレイヤー選択リスト
    view, no = e.UserSelect(view, no, block_id = "target_player", text = "対象プレイヤー")
    view, no = e.UserSelect(view, no, block_id = "vs_player", text = "対戦相手", add_list = ["全員"])

    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(view, no, text = "検索範囲設定", value = "click_versus", action_id = "modal-open-period")

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "click_personal", action_id = "actionId-versus")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")

    return(view)


@g.app.action("versus_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    g.logging.info(f"[global var] {g.app_var}")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = BuildVersusMenu(),
    )

@g.app.action("actionId-versus")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    b = body['view']['state']['values']
    p1 = list(b['target_player'].values())[0]['selected_option']['value']
    p2 = list(b['vs_player'].values())[0]['selected_option']['value']

    #command_option = f.configure.command_option_initialization("results")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{p1} vs {p2} の直接対戦を集計中…"),
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
        view_id = g.app_var["view_id"],
        view = BuildVersusMenu(),
    )
