"""
integrations/slack/events/home_tab/ui_parts.py
"""

import logging
from typing import cast

import libs.global_value as g
from integrations.protocols import MessageParserProtocol
from integrations.slack import config


def plain_text(msg: str) -> dict:
    """プレーンテキストの埋め込み

    Args:
        msg (str): テキスト

    Returns:
        dict: ブロック要素
    """

    view: dict = {"type": "home", "blocks": []}
    view["blocks"].append({"type": "section", "text": {}})
    view["blocks"][0]["text"] = {"type": "mrkdwn", "text": msg}

    return view


def divider() -> None:
    """境界線を引く"""
    g.app_config.tab_var["view"]["blocks"].append({"type": "divider", })
    g.app_config.tab_var["no"] += 1


def header(text: str = "dummy") -> None:
    """ヘッダ生成

    Args:
        text (str, optional): ヘッダテキスト. Defaults to "dummy".
    """

    g.app_config.tab_var["view"]["blocks"].append({"type": "header", "text": {}})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["text"] = {"type": "plain_text", "text": text}
    g.app_config.tab_var["no"] += 1


def button(text: str, action_id: str, style: str | bool = False) -> None:
    """ボタン配置

    Args:
        text (str, optional): 表示テキスト
        action_id (str): action_id
        style (str | bool, optional): 表示スタイル. Defaults to False.
    """

    g.app_config.tab_var["view"]["blocks"].append({"type": "actions", "elements": [{}]})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["elements"][0] = {"type": "button", "text": {}, "action_id": action_id}
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["elements"][0]["text"] = {"type": "plain_text", "text": text}
    if style:
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["elements"][0].update({"style": style})

    g.app_config.tab_var["no"] += 1


def radio_buttons(id_suffix: str, title: str, flag: dict) -> None:
    """オプション選択メニュー

    Args:
        id_suffix (str): block_id, action_id
        title (str): 表示タイトル
        flag (dict, optional): 表示する選択項目
    """

    g.app_config.tab_var["view"]["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["label"] = {"type": "plain_text", "text": title}
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["type"] = "radio_buttons"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["action_id"] = f"aid-{id_suffix}"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["initial_option"] = {  # 先頭の選択肢はチェック済みにする
        "text": {"type": "plain_text", "text": flag[next(iter(flag))]}, "value": next(iter(flag))
    }
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"] = []
    for k, v in flag.items():
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )
    g.app_config.tab_var["no"] += 1


def checkboxes(id_suffix: str, title: str, flag: dict | None = None, initial: list | None = None) -> None:
    """チェックボックス選択メニュー

    Args:
        id_suffix (str): block_id, action_id
        title (str): 表示タイトル
        flag (dict, optional): 表示する選択項目
        initial (list, optional): チェック済み項目. Defaults to None.
    """

    if flag is None:
        flag = {}

    g.app_config.tab_var["view"]["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["label"] = {"type": "plain_text", "text": title}
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["type"] = "checkboxes"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["action_id"] = f"aid-{id_suffix}"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"] = []
    if initial:
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["initial_options"] = []
    else:
        initial = []  # None -> list

    for k, v in flag.items():
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )
        if k in initial:
            g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["initial_options"].append(
                {"text": {"type": "plain_text", "text": v}, "value": k}
            )

    g.app_config.tab_var["no"] += 1


def user_select_pulldown(text: str = "dummy", add_list: list | None = None) -> None:
    """プレイヤー選択プルダウンメニュー

    Args:
        text (str, optional): 表示テキスト. Defaults to "dummy".
        add_list (list | None, optional): プレイヤーリスト. Defaults to None.
    """

    g.app_config.tab_var["view"]["blocks"].append({"type": "input", "block_id": "bid-user_select", "element": {}})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["type"] = "static_select"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["action_id"] = "player"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"] = []

    if add_list:
        for val in add_list:
            g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["label"] = {"type": "plain_text", "text": text}

    g.app_config.tab_var["no"] += 1


def multi_select_pulldown(text: str = "dummy", add_list: list | None = None) -> None:
    """複数プレイヤー選択プルダウンメニュー

    Args:
        text (str, optional): 表示テキスト. Defaults to "dummy".
        add_list (list | None, optional): プレイヤーリスト. Defaults to None.
    """
    g.app_config.tab_var["view"]["blocks"].append({"type": "input", "block_id": "bid-multi_select", "element": {}})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["type"] = "multi_static_select"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["action_id"] = "player"
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"] = []

    if add_list:
        for val in add_list:
            g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["label"] = {"type": "plain_text", "text": text}

    g.app_config.tab_var["no"] += 1


def input_ranked(block_id: str | bool = False) -> None:
    """ランキング上限入力テキストボックス

    Args:
        block_id (str | bool, optional): block_id. Defaults to False.
    """

    if block_id:
        g.app_config.tab_var["view"]["blocks"].append({"type": "input", "block_id": block_id, "element": {}, "label": {}})
    else:
        g.app_config.tab_var["view"]["blocks"].append({"type": "input", "element": {}, "label": {}})

    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"].update({"type": "number_input"})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"].update({"is_decimal_allowed": True})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"].update({"initial_value": str(g.cfg.ranking.ranked)})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"].update({"min_value": "1"})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["element"].update({"action_id": "aid-ranked"})
    g.app_config.tab_var["view"]["blocks"][g.app_config.tab_var["no"]]["label"].update({"type": "plain_text", "text": "出力順位上限"})

    g.app_config.tab_var["no"] += 1


def modalperiod_selection() -> dict:
    """日付選択

    Returns:
        dict: ブロック要素
    """

    view: dict = {"type": "modal", "callback_id": f"{g.app_config.tab_var["screen"]}_ModalPeriodSelection"}
    view["title"] = {"type": "plain_text", "text": "検索範囲指定"}
    view["submit"] = {"type": "plain_text", "text": "決定"}
    view["close"] = {"type": "plain_text", "text": "取消"}

    view["blocks"] = []
    view["blocks"].append({"type": "input", "element": {}, "label": {}})
    view["blocks"][0]["element"].update({"type": "datepicker"})
    view["blocks"][0]["element"].update({"initial_date": g.app_config.tab_var["sday"]})
    view["blocks"][0]["element"].update({"placeholder": {"type": "plain_text", "text": "Select a date"}})
    view["blocks"][0]["element"].update({"action_id": "aid-sday"})
    view["blocks"][0]["label"].update({"type": "plain_text", "text": "開始日"})
    view["blocks"].append({"type": "input", "element": {}, "label": {}})
    view["blocks"][1]["element"].update({"type": "datepicker"})
    view["blocks"][1]["element"].update({"initial_date": g.app_config.tab_var["eday"]})
    view["blocks"][1]["element"].update({"placeholder": {"type": "plain_text", "text": "Select a date"}})
    view["blocks"][1]["element"].update({"action_id": "aid-eday"})
    view["blocks"][1]["label"].update({"type": "plain_text", "text": "終了日"})

    return view


def set_command_option(body) -> tuple[list, list, dict]:
    """選択オプションの内容のフラグをセット

    Args:
        body (dict): イベント内容

    Returns:
        tuple[list, list, dict]:
        - list: コマンドに追加する文字列
        - list: viewに表示するメッセージ
        - dict: 変更されるフラグ
    """

    update_flag: dict = {}

    # 検索設定
    argument: list = []
    search_options = body["view"]["state"]["values"]
    logging.info("search options: %s", search_options)

    app_msg: list = []
    g.app_config.tab_var.update(operation=None)

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
                app_msg.append(f"集計範囲：{g.app_config.tab_var["sday"]} ～ {g.app_config.tab_var["eday"]}")
                argument.extend([g.app_config.tab_var["sday"], g.app_config.tab_var["eday"]])
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
                        update_flag.update(unregistered_replace=False)
                    case "versus_matrix":
                        update_flag.update(versus_matrix=True)
                    case "game_results":
                        update_flag.update(game_results=True)
                    case "verbose":
                        update_flag.update(game_results=True)
                        update_flag.update(verbose=True)
                    case "score_comparisons":
                        update_flag.update(score_comparisons=True)
                        g.app_config.tab_var.update(operation=None)
                    case _ as option:
                        g.app_config.tab_var.update(operation=option)

    app_msg.append("集計中…")
    return (argument, app_msg, update_flag)


def update_view(m: MessageParserProtocol, msg: list):
    """viewを更新する

    Args:
        m (MessageParserProtocol): メッセージデータ
        msg (list): 表示テキスト
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    if isinstance(m.post.headline, dict):
        k, v = next(iter(m.post.headline.items()))
        text = f"\n【{k}】\n{v}"
    else:
        text = m.post.headline

    g.app_config.appclient.views_update(
        view_id=g.app_config.tab_var["view_id"],
        view=plain_text(f"{chr(10).join(msg)}\n\n{text}".strip()),
    )
