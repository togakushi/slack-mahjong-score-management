from datetime import datetime

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def PlainText(msg):
    view = {"type": "home", "blocks": []}
    view["blocks"].append({"type": "section", "text": {}})
    view["blocks"][0]["text"] = {"type": "mrkdwn", "text": msg}

    return(view)


def Divider(view, no):
    view["blocks"].append({"type": "divider",})

    return(view, no + 1)


def Header(view, no, text = "dummy"):
    view["blocks"].append({"type": "header", "text": {}})
    view["blocks"][no]["text"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def Button(view, no, text = "Click Me", value = "dummy", action_id = False, style = False):
    view["blocks"].append({"type": "actions", "elements": [{}]})
    view["blocks"][no]["elements"][0] = {"type": "button", "text": {}, "value": value, "action_id": action_id}
    view["blocks"][no]["elements"][0]["text"] = {"type": "plain_text", "text": text}

    if style:
        view["blocks"][no]["elements"][0].update({"style": style})

    return(view, no + 1)


def SearchOptions(view, no, flag = []):
    view["blocks"].append(
        {"type": "input", "block_id": "bid-search_option", "optional": False, "element": {}}
    )
    view["blocks"][no]["label"] = {"type": "plain_text", "text": "検索オプション"}
    view["blocks"][no]["element"]["type"] = "checkboxes"
    view["blocks"][no]["element"]["action_id"] =  "aid-search"

    view["blocks"][no]["element"]["options"] = []
    view["blocks"][no]["element"]["initial_options"] = []

    if "unregistered_replace" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "ゲスト無効"}, "value": "unregistered_replace"}
        )
        view["blocks"][no]["element"]["initial_options"].append(
            {"text": {"type": "plain_text", "text": "ゲスト無効"}, "value": "unregistered_replace"}
        )

    if "archive" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "アーカイブ"}, "value": "archive"}
        )

    return(view, no + 1)


def DisplayOptions(view, no, flag = []):
    view["blocks"].append(
        {"type": "input", "block_id": "bid-display_option", "optional": False, "element": {}}
    )
    view["blocks"][no]["label"] = {"type": "plain_text", "text": "表示オプション"}
    view["blocks"][no]["element"]["type"] = "checkboxes"
    view["blocks"][no]["element"]["action_id"] =  "aid-display"

    view["blocks"][no]["element"]["options"] = []
    #view["blocks"][no]["element"]["initial_options"] = []

    if "versus_matrix" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "対戦結果"}, "value": "versus_matrix"}
        )

    if "game_results" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "戦績（簡易）"}, "value": "game_results"}
        )

    if "verbose" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "戦績（詳細）"}, "value": "verbose"}
        )

    if "score_comparisons" in flag:
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": "累積ポイント比較"}, "value": "score_comparisons"}
        )

    return(view, no + 1)


def UserSelect(view, no, text = "dummy", add_list = False):
    view["blocks"].append({"type": "input", "block_id": "bid-user_select", "element": {}})
    view["blocks"][no]["element"]["type"] = "static_select"
    view["blocks"][no]["element"]["action_id"] = "player"
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    view["blocks"][no]["element"]["options"] = []

    if add_list:
        for i in range(len(add_list)):
            view["blocks"][no]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": add_list[i]}, "value": add_list[i]}
            )

    for name in c.GetMemberList():
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def MultiSelect(view, no, text = "dummy", add_list = False):
    view["blocks"].append({"type": "input", "block_id": "bid-multi_select", "element": {}})
    view["blocks"][no]["element"]["type"] = "multi_static_select"
    view["blocks"][no]["element"]["action_id"] = "player"
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    view["blocks"][no]["element"]["options"] = []

    if add_list:
        for i in range(len(add_list)):
            view["blocks"][no]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": add_list[i]}, "value": add_list[i]}
            )

    for name in c.GetMemberList():
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def PeriodSelection(view, no, text = "dummy", block_id = False, action_id = "dummy", initial_date = False):
    if not initial_date:
        initial_date = (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d")
 
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}})

    view["blocks"][no]["element"]["type"] = "datepicker"
    view["blocks"][no]["element"]["initial_date"] = initial_date
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select a date"}
    view["blocks"][no]["element"]["action_id"] =  action_id
    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def SearchRangeChoice(view, no):
    days = f"{g.app_var['sday']} ～ {g.app_var['eday']}"
    view["blocks"].append({"type": "input", "block_id": "bid-search_range", "element": {}})
    view["blocks"][no]["label"] = {"type": "plain_text", "text": "検索範囲"}
    view["blocks"][no]["element"]["type"] = "radio_buttons"
    view["blocks"][no]["element"]["action_id"] = "aid-range"

    view["blocks"][no]["element"]["initial_option"] = {}
    view["blocks"][no]["element"]["initial_option"]["text"] = {"type": "plain_text", "text": f"範囲指定： {days}"}
    view["blocks"][no]["element"]["initial_option"]["value"] = "指定"
    view["blocks"][no]["element"]["options"] = []
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "今月"}, "value": "今月"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "先月"}, "value": "先月"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "全部"}, "value": "全部"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": f"範囲指定： {days}"}, "value": "指定"}
    )

    return(view, no + 1)


def InputRanked(view, no, block_id = False):
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}, "label": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}, "label": {}})

    view["blocks"][no]["element"].update({"type": "number_input"})
    view["blocks"][no]["element"].update({"is_decimal_allowed": True})
    view["blocks"][no]["element"].update({"initial_value": str(g.config["ranking"].getint("ranked", 3))})
    view["blocks"][no]["element"].update({"min_value": "1"})
    view["blocks"][no]["element"].update({"action_id": "aid-ranked"})
    view["blocks"][no]["label"].update({"type": "plain_text", "text": "出力順位上限"})

    return(view, no + 1)


def ModalPeriodSelection():
    view = {"type": "modal", "callback_id": f"{g.app_var['screen']}_ModalPeriodSelection"}
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

    return(view)


#		{
#			"type": "input",
#			"element": {
#				"type": "plain_text_input",
#				"action_id": "plain_text_input-action"
#			},
#			"label": {
#				"type": "plain_text",
#				"text": "直近のN回"
#			}
#		}
#	]
#}
