"""
lib/home_tab/home.py
"""

import logging

import lib.global_value as g
from lib import home_tab as h


def build_main_menu():
    """メインメニューを生成する"""
    g.app_var["screen"] = "MainMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    h.ui_parts.button(text="成績サマリ", action_id="summary_menu")
    h.ui_parts.button(text="ランキング", action_id="ranking_menu")
    h.ui_parts.button(text="個人成績", action_id="personal_menu")
    h.ui_parts.button(text="直接対戦", action_id="versus_menu")


def set_command_option(body):
    """選択オプションの内容のフラグをセット

    Args:
        body (dict): イベント内容

    Returns:
        Tuple[list, list]:
            - list: コマンドに追加する文字列
            - list: viewに表示するメッセージ
    """

    # 検索設定
    argument: list = []
    search_options = body["view"]["state"]["values"]
    logging.info("search options: %s", search_options)

    app_msg: list = []
    g.app_var.update(operation=None)

    if "bid-user_select" in search_options:
        user_select = search_options["bid-user_select"]["player"]["selected_option"]
        if user_select is not None:
            if "value" in user_select:
                player = user_select["value"]
                app_msg.append(f"対象プレイヤー：{player}")
                argument.append(player)

    if "bid-multi_select" in search_options:
        user_list = search_options["bid-multi_select"]["player"]["selected_options"]
        for _, val in enumerate(user_list):
            argument.append(val["value"])

    if "bid-search_range" in search_options:
        match search_options["bid-search_range"]["aid-search_range"]["selected_option"]["value"]:
            case "指定":
                app_msg.append(f"集計範囲：{g.app_var['sday']} ～ {g.app_var['eday']}")
                argument.extend([g.app_var["sday"], g.app_var["eday"]])
            case "全部":
                app_msg.append("集計範囲：全部")
                argument.append("全部")
            case _ as select_item:
                app_msg.append(f"集計範囲：{select_item}")
                argument.append(select_item)

    for id_suffix in ("search_option", "display_option", "output_option"):
        if f"bid-{id_suffix}" in search_options:
            match search_options[f"bid-{id_suffix}"][f"aid-{id_suffix}"].get("type"):
                case "checkboxes":
                    selected_options = search_options[f"bid-{id_suffix}"][f"aid-{id_suffix}"].get("selected_options")
                case "radio_buttons":
                    selected_options = [search_options[f"bid-{id_suffix}"][f"aid-{id_suffix}"].get("selected_option")]
                case _:
                    continue

            for _, val in enumerate(selected_options):
                match val["value"]:
                    case "unregistered_replace":
                        g.opt.unregistered_replace = False
                    case "versus_matrix":
                        g.opt.versus_matrix = True
                    case "game_results":
                        g.opt.game_results = True
                    case "verbose":
                        g.opt.game_results = True
                        g.opt.verbose = True
                    case "score_comparisons":
                        g.opt.score_comparisons = True
                        g.app_var.update(operation=None)
                    case _ as option:
                        g.app_var.update(operation=option)

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
    logging.trace(body)  # type: ignore

    build_main_menu()
    client.views_publish(
        user_id=g.app_var["user_id"],
        view=g.app_var["view"],
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
        view=h.ui_parts.modalperiod_selection(),
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
