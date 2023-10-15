import lib.event as e
from lib.function import global_value as g


def BuildPersonalMenu():
    g.app_var["screen"] = "PersonalMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = e.Header(view, no, "【個人成績】")

    # プレイヤー選択リスト
    view, no = e.UserSelect(view, no, block_id = "target_player", text = "対象プレイヤー")

    # 検索範囲設定
    view, no = e.Divider(view, no)
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.Button(view, no, text = "検索範囲設定", value = "click_versus", action_id = "modal-open-period")

    # 検索オプション
    view, no = e.Divider(view, no)
    view, no = e.SearchOptions(view, no, block_id = "bid-option")

    view, no = e.Divider(view, no)
    view, no = e.Button(view, no, text = "集計開始", value = "click_personal", action_id = "actionId-personal")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")

    return(view)


@g.app.action("personal_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    g.app_var["view_id"] = body["view"]["id"]
    g.logging.info(f"[personal_menu] {g.app_var}")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = BuildPersonalMenu(),
    )


@g.app.action("actionId-personal")
def handle_some_action(ack, body, view, client):
    ack()
    g.logging.trace(body)
    g.logging.info(body)

    b = body['view']['state']['values']
    p1 = list(b['target_player'].values())[0]['selected_option']['value']

    #command_option = f.configure.command_option_initialization("results")

    client.views_update(
        view_id = g.app_var["view_id"],
        view = e.PlainText(f"{p1} の成績を集計中…")
    )
