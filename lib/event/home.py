import logging

import global_value as g
from lib import event as e


@g.app.event("app_home_opened")
def handle_home_events(client, event):
    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    logging.trace(f"{g.app_var}")  # type: ignore

    result = client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_main_menu(),
    )

    logging.trace(result)  # type: ignore


def build_main_menu():
    g.app_var["screen"] = "MainMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = e.ui_parts.Button(view, no, text="成績サマリ", value="click_summary_menu", action_id="menu_summary")
    view, no = e.ui_parts.Button(view, no, text="ランキング", value="click_ranking_menu", action_id="menu_ranking")
    view, no = e.ui_parts.Button(view, no, text="個人成績", value="click_personal_menu", action_id="menu_personal")
    view, no = e.ui_parts.Button(view, no, text="直接対戦", value="click_versus_menu", action_id="menu_versus")

    return (view)


def set_command_option(body):
    # 検索設定
    argument = []
    search_options = body["view"]["state"]["values"]
    logging.info(f"search options: {search_options}")

    app_msg = []

    if "bid-user_select" in search_options:
        user_select = search_options["bid-user_select"]["player"]["selected_option"]
        if user_select is not None:
            if "value" in user_select:
                player = user_select["value"]
                app_msg.append(f"対象プレイヤー： {player}")
                argument.append(player)

    if "bid-multi_select" in search_options:
        user_list = search_options["bid-multi_select"]["player"]["selected_options"]
        for i in range(len(user_list)):
            argument.append(user_list[i]["value"])

    if "bid-search_range" in search_options:
        select_item = search_options["bid-search_range"]["aid-range"]["selected_option"]["value"]
        if select_item == "指定":
            app_msg.append(f"集計範囲： {g.app_var['sday']} ～ {g.app_var['eday']}")
            argument.append(g.app_var["sday"].replace("-", ""))
            argument.append(g.app_var["eday"].replace("-", ""))
        elif select_item == "全部":
            app_msg.append("集計範囲： 全部")
            argument.append("全部")
        else:
            app_msg.append(f"集計範囲： {select_item}")
            argument.append(select_item)

    if "bid-search_option" in search_options:
        selected_options = search_options["bid-search_option"]["aid-search"]["selected_options"]
        for i in range(len(selected_options)):
            flag = selected_options[i]["value"]
            if flag == "unregistered_replace":
                g.opt.unregistered_replace = False

    if "bid-display_option" in search_options:
        selected_options = search_options["bid-display_option"]["aid-display"]["selected_options"]
        for i in range(len(selected_options)):
            flag = selected_options[i]["value"]
            if flag == "versus_matrix":
                g.opt.versus_matrix = True
            if flag == "game_results":
                g.opt.game_results = True
            if flag == "verbose":
                g.opt.game_results = True
                g.opt.verbose = True
            if flag == "score_comparisons":
                g.opt.score_comparisons = True

    app_msg.append("集計中…")
    return (argument, app_msg)


@g.app.action("actionId-back")
def handle_action(ack, body, client):
    ack()
    logging.trace(body)  # type: ignore

    client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_main_menu(),
    )


@g.app.action("modal-open-period")
def handle_open_modal_button_clicks(ack, body, client):
    ack()

    client.views_open(
        trigger_id=body["trigger_id"],
        view=e.ui_parts.ModalPeriodSelection(),
    )


@g.app.action("debug")
def handle_debug_action(ack, body):
    ack()

    x = body['view']['state']['values']
    print("-" * 15)
    print(x.keys())
    print(x)
