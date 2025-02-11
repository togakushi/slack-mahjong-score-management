import logging

import global_value as g
from lib import home_tab as h


def build_main_menu():
    """メインメニューを生成する

    Returns:
        dict: viewに描写する内容
    """

    g.app_var["screen"] = "MainMenu"
    no = 0
    view = {"type": "home", "blocks": []}
    view, no = h.ui_parts.Button(view, no, text="成績サマリ", action_id="summary_menu")
    view, no = h.ui_parts.Button(view, no, text="ランキング", action_id="ranking_menu")
    view, no = h.ui_parts.Button(view, no, text="個人成績", action_id="personal_menu")
    view, no = h.ui_parts.Button(view, no, text="直接対戦", action_id="versus_menu")

    return (view)


def set_command_option(body):
    """オプションのボタンを配置する

    Args:
        body (dict): イベント内容

    Returns:
        dict: viewに描写する内容
    """

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
                app_msg.append(f"対象プレイヤー：{player}")
                argument.append(player)

    if "bid-multi_select" in search_options:
        user_list = search_options["bid-multi_select"]["player"]["selected_options"]
        for i in range(len(user_list)):
            argument.append(user_list[i]["value"])

    if "bid-search_range" in search_options:
        match search_options["bid-search_range"]["aid-range"]["selected_option"]["value"]:
            case "指定":
                app_msg.append(f"集計範囲：{g.app_var['sday']} ～ {g.app_var['eday']}")
                argument.extend([g.app_var["sday"], g.app_var["eday"]])
            case "全部":
                app_msg.append("集計範囲：全部")
                argument.append("全部")
            case _ as select_item:
                app_msg.append(f"集計範囲：{select_item}")
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
            match selected_options[i]["value"]:
                case "versus_matrix":
                    g.opt.versus_matrix = True
                case "game_results":
                    g.opt.game_results = True
                case "verbose":
                    g.opt.game_results = True
                    g.opt.verbose = True
                case "score_comparisons":
                    g.opt.score_comparisons = True

    app_msg.append("集計中…")
    return (argument, app_msg)


@g.app.action("actionId-back")
def handle_action(ack, body, client):
    """戻るボタン

    Args:
        ack (_type_): ack
        body (dict): イベント内容
        client (slack_bolt.App.client): slack_boltオブジェクト
    """

    ack()
    logging.trace(body)

    client.views_publish(
        user_id=g.app_var["user_id"],
        view=build_main_menu(),
    )


@g.app.action("modal-open-period")
def handle_open_modal_button_clicks(ack, body, client):
    """検索範囲設定選択イベント

    Args:
        ack (_type_): ack
        body (dict): イベント内容
        client (slack_bolt.App.client): オブジェクト
    """

    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=h.ui_parts.ModalPeriodSelection(),
    )


@g.app.action("debug")
def handle_debug_action(ack, body):
    """デバッグ用

    Args:
        ack (_type_): ack
        body (dict): イベント内容
    """

    ack()
    x = body['view']['state']['values']
    print("-" * 15)
    print(x.keys())
    print(x)
