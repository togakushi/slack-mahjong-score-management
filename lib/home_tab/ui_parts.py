from datetime import datetime
from typing import Tuple

from dateutil.relativedelta import relativedelta

import lib.global_value as g


def plain_text(msg: str) -> dict:
    view: dict = {"type": "home", "blocks": []}
    view["blocks"].append({"type": "section", "text": {}})
    view["blocks"][0]["text"] = {"type": "mrkdwn", "text": msg}

    return (view)


def divider(view: dict, no: int) -> Tuple[dict, int]:
    view["blocks"].append({"type": "divider", })

    return (view, no + 1)


def header(view: dict, no: int, text: str = "dummy") -> Tuple[dict, int]:
    view["blocks"].append({"type": "header", "text": {}})
    view["blocks"][no]["text"] = {"type": "plain_text", "text": text}

    return (view, no + 1)


def button(view: dict, no: int, text: str = "Click Me", action_id: str | bool = False, style: str | bool = False) -> Tuple[dict, int]:
    view["blocks"].append({"type": "actions", "elements": [{}]})
    view["blocks"][no]["elements"][0] = {"type": "button", "text": {}, "action_id": action_id}
    view["blocks"][no]["elements"][0]["text"] = {"type": "plain_text", "text": text}

    if style:
        view["blocks"][no]["elements"][0].update({"style": style})

    return (view, no + 1)


def radio_buttons(view: dict, no: int, id_suffix: str, title: str, flag: dict) -> Tuple[dict, int]:
    """オプション選択メニュー

    Args:
        view (dict): 描写内容
        no (int): ブロックNo
        id_suffix (str): block_id, action_id
        title (str): 表示タイトル
        flag (dict, optional): 表示する選択項目

    Returns:
        Tuple[dict, int]:
            - dict: 描写内容
            - int: 次のブロックNo
    """

    view["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    view["blocks"][no]["label"] = {"type": "plain_text", "text": title}
    view["blocks"][no]["element"]["type"] = "radio_buttons"
    view["blocks"][no]["element"]["action_id"] = f"aid-{id_suffix}"
    view["blocks"][no]["element"]["initial_option"] = {  # 先頭の選択肢はチェック済みにする
        "text": {"type": "plain_text", "text": flag[next(iter(flag))]}, "value": next(iter(flag))
    }
    view["blocks"][no]["element"]["options"] = []
    for k, v in flag.items():
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )

    return (view, no + 1)


def checkboxes(view: dict, no: int, id_suffix: str, title: str, flag: dict | None = None, initial: list | None = None) -> Tuple[dict, int]:
    """チェックボックス選択メニュー

    Args:
        view (dict): 描写内容
        no (int): ブロックNo
        id_suffix (str): block_id, action_id
        title (str): 表示タイトル
        flag (dict, optional): 表示する選択項目
        initial (list, optional): チェック済み項目. Defaults to None.

    Returns:
        Tuple[dict, int]:
            - dict: 描写内容
            - int: 次のブロックNo
    """

    if flag is None:
        flag = {}

    view["blocks"].append({"type": "input", "block_id": f"bid-{id_suffix}", "element": {}})
    view["blocks"][no]["label"] = {"type": "plain_text", "text": title}
    view["blocks"][no]["element"]["type"] = "checkboxes"
    view["blocks"][no]["element"]["action_id"] = f"aid-{id_suffix}"
    view["blocks"][no]["element"]["options"] = []
    if initial:
        view["blocks"][no]["element"]["initial_options"] = []
    else:
        initial = []  # None -> list

    for k, v in flag.items():
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": v}, "value": k}
        )
        if k in initial:
            view["blocks"][no]["element"]["initial_options"].append(
                {"text": {"type": "plain_text", "text": v}, "value": k}
            )

    return (view, no + 1)


def user_select(view: dict, no: int, text: str = "dummy", add_list: list | None = None) -> Tuple[dict, int]:
    view["blocks"].append({"type": "input", "block_id": "bid-user_select", "element": {}})
    view["blocks"][no]["element"]["type"] = "static_select"
    view["blocks"][no]["element"]["action_id"] = "player"
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    view["blocks"][no]["element"]["options"] = []

    if add_list:
        for val in add_list:
            view["blocks"][no]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return (view, no + 1)


def multi_select(view: dict, no: int, text: str = "dummy", add_list: list | None = None) -> Tuple[dict, int]:
    view["blocks"].append({"type": "input", "block_id": "bid-multi_select", "element": {}})
    view["blocks"][no]["element"]["type"] = "multi_static_select"
    view["blocks"][no]["element"]["action_id"] = "player"
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    view["blocks"][no]["element"]["options"] = []

    if add_list:
        for val in add_list:
            view["blocks"][no]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": val}, "value": val}
            )

    for name in set(g.member_list.values()):
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return (view, no + 1)


def period_selection(view: dict, no: int, text: str = "dummy", block_id: str | bool = False, action_id: str = "dummy", initial_date: str | bool = False) -> Tuple[dict, int]:
    if not initial_date:
        initial_date = (
            datetime.now() + relativedelta(hours=-12)
        ).strftime("%Y-%m-%d")

    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}})

    view["blocks"][no]["element"]["type"] = "datepicker"
    view["blocks"][no]["element"]["initial_date"] = initial_date
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select a date"}
    view["blocks"][no]["element"]["action_id"] = action_id
    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return (view, no + 1)


def input_ranked(view: dict, no: int, block_id: str | bool = False) -> Tuple[dict, int]:
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}, "label": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}, "label": {}})

    view["blocks"][no]["element"].update({"type": "number_input"})
    view["blocks"][no]["element"].update({"is_decimal_allowed": True})
    view["blocks"][no]["element"].update({"initial_value": str(g.cfg.config["ranking"].getint("ranked", 3))})
    view["blocks"][no]["element"].update({"min_value": "1"})
    view["blocks"][no]["element"].update({"action_id": "aid-ranked"})
    view["blocks"][no]["label"].update({"type": "plain_text", "text": "出力順位上限"})

    return (view, no + 1)


def modalperiod_selection() -> dict:
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
