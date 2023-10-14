from datetime import datetime

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def PlainText(msg):
    view = {}
    view["type"] = "home"
    view["blocks"] = []
    view["blocks"].append({"type": "section", "text": {}})
    view["blocks"][0]["text"] = {"type": "plain_text", "text": msg}

    return(view)


def Header(view, no, text = "dummy"):
    view["blocks"].append({"type": "header", "text": {}})
    view["blocks"][no]["text"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def Button(view, no, text = "dummy", value = "dummy", action_id = False):
    view["blocks"].append({"type": "actions", "elements": [{}]})
    view["blocks"][no]["elements"][0] = {"type": "button", "text": {}, "value": value, "action_id": action_id}
    view["blocks"][no]["elements"][0]["text"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def SearchOptions(view, no, block_id = False):
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}})

    view["blocks"][no]["label"] = {"type": "plain_text", "text": "検索オプション"}
    view["blocks"][no]["element"]["type"] = "checkboxes"
    view["blocks"][no]["element"]["action_id"] =  "aid-checkboxes"

    view["blocks"][no]["element"]["options"] = []
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "ゲスト無効"}, "value": "unregistered_replace"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "アーカイブ"}, "value": "archive"}
    )

    view["blocks"][no]["element"]["initial_options"] = []
    view["blocks"][no]["element"]["initial_options"].append(
        {"text": {"type": "plain_text", "text": "ゲスト無効"}, "value": "unregistered_replace"}
    )

    return(view, no + 1)


def UserSelect(view, no, text = "dummy", block_id = False, add_list = False):
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}})

    view["blocks"][no]["element"]["type"] = "static_select"
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select an item"}
    view["blocks"][no]["element"]["options"] = []

    if add_list:
        for i in range(len(add_list)):
            view["blocks"][no]["element"]["options"].append(
                {"text": {"type": "plain_text", "text": add_list[i]}, "value": add_list[i]}
            )

    for name in c.GetMemberName():
        view["blocks"][no]["element"]["options"].append(
            {"text": {"type": "plain_text", "text": name}, "value": name}
        )

    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def PeriodSelection(view, no, text = "dummy", block_id = False, action_id = "dummy"):
    if block_id:
        view["blocks"].append({"type": "input", "block_id": block_id, "element": {}})
    else:
        view["blocks"].append({"type": "input", "element": {}})

    view["blocks"][no]["element"]["type"] = "datepicker"
    view["blocks"][no]["element"]["initial_date"] = (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d")
    view["blocks"][no]["element"]["placeholder"] = {"type": "plain_text", "text": "Select a date"}
    view["blocks"][no]["element"]["action_id"] =  action_id
    view["blocks"][no]["label"] = {"type": "plain_text", "text": text}

    return(view, no + 1)


def SearchRangeChoice(view, no):
    view["blocks"].append({"type": "input", "element": {}})
    view["blocks"][no]["label"] = {"type": "plain_text", "text": "検索範囲"}
    view["blocks"][no]["element"]["type"] = "radio_buttons"
    view["blocks"][no]["element"]["action_id"] = "radio_buttons"
    view["blocks"][no]["element"]["initial_option"] = {}
    view["blocks"][no]["element"]["initial_option"]["text"] = {"type": "plain_text", "text": "範囲選択 / 回数指定"}
    view["blocks"][no]["element"]["initial_option"]["value"] = "選択"

    view["blocks"][no]["element"]["options"] = []
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "範囲選択 / 回数指定"}, "value": "選択"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "今月"}, "value": "今月"}
    )
    view["blocks"][no]["element"]["options"].append(
        {"text": {"type": "plain_text", "text": "全部"}, "value": "全部"}
    )

    return(view, no + 1)

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
