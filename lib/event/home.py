import lib.event as e
from lib.function import global_value as g


def BuildMainMenu():
    g.app_var["screen"] = "MainMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = e.Button(view, no, text = "成績サマリ", value = "click_summary_menu", action_id = "menu_summary")
    view, no = e.Button(view, no, text = "ランキング", value = "click_ranking_menu", action_id = "menu_ranking")
    #view, no = e.Button(view, no, text = "個人成績", value = "click_personal_menu", action_id = "personal_menu")
    #view, no = e.Button(view, no, text = "直接対戦", value = "click_versus_menu", action_id = "versus_menu")

    return(view)


def SetCommandOption(command_option, body):
    # 検索設定
    search_options = body["view"]["state"]["values"]
    g.logging.info(f"[app:search options] {search_options}")

    app_msg = "集計中…"

    if "bid-range" in search_options:
        select_item = search_options["bid-range"]["aid-range"]["selected_option"]["value"]
        if select_item == "指定":
            app_msg = f"{g.app_var['sday']} ～ {g.app_var['eday']} の結果を集計中…"
            command_option["aggregation_range"].append(g.app_var["sday"].replace("-",""))
            command_option["aggregation_range"].append(g.app_var["eday"].replace("-",""))
        elif select_item == "全部":
            command_option["aggregation_range"].append("全部")
        else:
            app_msg = f"{select_item}の結果を集計中…"
            command_option["aggregation_range"].append(select_item)

    if "bid-option" in search_options:
        selected_options = search_options["bid-option"]["aid-option"]["selected_options"]
        for i in range(len(selected_options)):
            flag = selected_options[i]["value"]
            if flag == "unregistered_replace":
                command_option[flag] = False
            if flag == "archive":
                command_option[flag] = True

    if "bid-ranked" in search_options:
        ranked = int(search_options["bid-ranked"]["aid-ranked"]["value"])
        if ranked > 0:
            command_option["ranked"] = ranked

    g.logging.info(command_option)
    return(command_option, app_msg)


@g.app.action("actionId-back")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    client.views_publish(
        user_id = g.app_var["user_id"],
        view = BuildMainMenu(),
    )


@g.app.action("modal-open-period")
def handle_open_modal_button_clicks(ack, body, client):
    ack()

    client.views_open(
        trigger_id = body["trigger_id"],
        view =e.ModalPeriodSelection(),
    )


@g.app.action("debug")
def handle_some_action(ack, body):
    ack()

    x = body['view']['state']['values']
    print("-" * 15)
    print(x.keys())
    print(x)
