"""
lib/home_tab/ui_parts.py
"""

import lib.global_value as g


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

    return (view)


def divider() -> None:
    """境界線を引く"""
    g.app_var["view"]["blocks"].append({"type": "divider", })
    g.app_var["no"] += 1


def header(text: str = "dummy") -> None:
    """ヘッダ生成

    Args:
        text (str, optional): ヘッダテキスト. Defaults to "dummy".
    """

    g.app_var["view"]["blocks"].append({"type": "header", "text": {}})
    g.app_var["view"]["blocks"][g.app_var["no"]]["text"] = {"type": "plain_text", "text": text}
    g.app_var["no"] += 1


def button(text: str, action_id: str, style: str | bool = False) -> None:
    """ボタン配置

    Args:
        text (str, optional): 表示テキスト
        action_id (str): action_id
        style (str | bool, optional): 表示スタイル. Defaults to False.
    """

    g.app_var["view"]["blocks"].append({"type": "actions", "elements": [{}]})
    g.app_var["view"]["blocks"][g.app_var["no"]]["elements"][0] = {"type": "button", "text": {}, "action_id": action_id}
    g.app_var["view"]["blocks"][g.app_var["no"]]["elements"][0]["text"] = {"type": "plain_text", "text": text}
    if style:
        g.app_var["view"]["blocks"][g.app_var["no"]]["elements"][0].update({"style": style})

    g.app_var["no"] += 1


def radio_buttons(id_suffix: str, title: str, flag: dict) -> None:
    """オプション選択メニュー

    Args:
        id_suffix (str): block_id, action_id
        title (str): 表示タイトル
        flag (dict, optional): 表示する選択項目
    """

    g.app_var["view"]["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    g.app_var["view"]["blocks"][g.app_var["no"]]["label"] = {"type": "plain_text", "text": title}
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["type"] = "radio_buttons"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["action_id"] = f"aid-{id_suffix}"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["initial_option"] = {  # 先頭の選択肢はチェック済みにする
        "text": {"type": "plain_text", "text": flag[next(iter(flag))]}, "value": next(iter(flag))
    }
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"] = []
    for k, v in flag.items():
        g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )
    g.app_var["no"] += 1


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

    g.app_var["view"]["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    g.app_var["view"]["blocks"][g.app_var["no"]]["label"] = {"type": "plain_text", "text": title}
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["type"] = "checkboxes"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["action_id"] = f"aid-{id_suffix}"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"] = []
    if initial:
        g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["initial_options"] = []
    else:
        initial = []  # None -> list

    for k, v in flag.items():
        g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )
        if k in initial:
            g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["initial_options"].append(
                {"text": {"type": "plain_text", "text": v}, "value": k}
            )

    g.app_var["no"] += 1


def user_select(text: str = "dummy", add_list: list | None = None) -> None:
    """プレイヤー選択プルダウンメニュー

    Args:
        text (str, optional): 表示テキスト. Defaults to "dummy".
        add_list (list | None, optional): プレイヤーリスト. Defaults to None.
    """

    g.app_var["view"]["blocks"].append({"type": "input", "block_id": "bid-user_select", "element": {}})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["type"] = "static_select"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["action_id"] = "player"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"] = []

    if add_list:
        for val in add_list:
            g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    g.app_var["view"]["blocks"][g.app_var["no"]]["label"] = {"type": "plain_text", "text": text}

    g.app_var["no"] += 1


def multi_select(text: str = "dummy", add_list: list | None = None) -> None:
    """複数プレイヤー選択プルダウンメニュー

    Args:
        text (str, optional): 表示テキスト. Defaults to "dummy".
        add_list (list | None, optional): プレイヤーリスト. Defaults to None.
    """
    g.app_var["view"]["blocks"].append({"type": "input", "block_id": "bid-multi_select", "element": {}})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["type"] = "multi_static_select"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["action_id"] = "player"
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"] = []

    if add_list:
        for val in add_list:
            g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        g.app_var["view"]["blocks"][g.app_var["no"]]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    g.app_var["view"]["blocks"][g.app_var["no"]]["label"] = {"type": "plain_text", "text": text}

    g.app_var["no"] += 1


def input_ranked(block_id: str | bool = False) -> None:
    """ランキング上限入力テキストボックス

    Args:
        block_id (str | bool, optional): block_id. Defaults to False.
    """

    if block_id:
        g.app_var["view"]["blocks"].append({"type": "input", "block_id": block_id, "element": {}, "label": {}})
    else:
        g.app_var["view"]["blocks"].append({"type": "input", "element": {}, "label": {}})

    g.app_var["view"]["blocks"][g.app_var["no"]]["element"].update({"type": "number_input"})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"].update({"is_decimal_allowed": True})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"].update({"initial_value": str(g.cfg.config["ranking"].getint("ranked", 3))})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"].update({"min_value": "1"})
    g.app_var["view"]["blocks"][g.app_var["no"]]["element"].update({"action_id": "aid-ranked"})
    g.app_var["view"]["blocks"][g.app_var["no"]]["label"].update({"type": "plain_text", "text": "出力順位上限"})

    g.app_var["no"] += 1


def modalperiod_selection() -> dict:
    """日付選択

    Returns:
        dict: ブロック要素
    """

    view: dict = {"type": "modal", "callback_id": f"{g.app_var['screen']}_ModalPeriodSelection"}
    view["title"] = {"type": "plain_text", "text": "検索範囲指定"}
    view["submit"] = {"type": "plain_text", "text": "決定"}
    view["close"] = {"type": "plain_text", "text": "取消"}

    view["blocks"] = []
    view["blocks"].append({"type": "input", "element": {}, "label": {}})
    view["blocks"][0]["element"].update({"type": "datepicker"})
    view["blocks"][0]["element"].update({"initial_date": g.app_var["sday"]})
    view["blocks"][0]["element"].update({"placeholder": {"type": "plain_text", "text": "Select a date"}})
    view["blocks"][0]["element"].update({"action_id": "aid-sday"})
    view["blocks"][0]["label"].update({"type": "plain_text", "text": "開始日"})
    view["blocks"].append({"type": "input", "element": {}, "label": {}})
    view["blocks"][1]["element"].update({"type": "datepicker"})
    view["blocks"][1]["element"].update({"initial_date": g.app_var["eday"]})
    view["blocks"][1]["element"].update({"placeholder": {"type": "plain_text", "text": "Select a date"}})
    view["blocks"][1]["element"].update({"action_id": "aid-eday"})
    view["blocks"][1]["label"].update({"type": "plain_text", "text": "終了日"})

    return (view)
