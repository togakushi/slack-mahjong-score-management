import json
from datetime import datetime

from dateutil.relativedelta import relativedelta

import command as c
import function as f
from function import global_value as g


@g.app.action("actionId-personal_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    user_list = []
    for name in c.GetMemberName():
        user_list.append(
            '{"text": {"type": "plain_text", "text": "' + name + '"}, "value": "' + name + '"}'
        )

    user_id = body["user"]["id"]
    initial_date = (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d")
    result = client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "対戦相手の選択"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select an item"
                        },
                        "options": [
                            ",\n".join([i for i in user_list])
                        ],
                        "action_id": "static_select-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "対象プレイヤー"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select an item"
                        },
                        "options": [
                            {"text": {"type": "plain_text", "text": "いけどん"},"value": "いけどん"}
                        ],
                        "action_id": "static_select-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "対戦プレイヤー"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "未登録プレイヤーを直接指定"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": "対戦相手を空欄にした場合は全員が対象"
                        }
                    ]
                },
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "集計期間"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "radio_buttons",
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "今月"
                                },
                                "value": "value-0"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "先月"
                                },
                                "value": "value-1"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "全部"
                                },
                                "value": "value-2"
                            }
                        ],
                        "action_id": "radio_buttons-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "キーワード指定"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "datepicker",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "datepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "検索開始日"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "datepicker",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "datepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "検索終了日"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "集計開始"
                            },
                            "value": "click_me_123",
                            "action_id": "actionId-0"
                        }
                    ]
                }
            ]
        }
    )

    g.logging.trace(result)

@g.app.action("actionId-search")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    command_option = f.configure.command_option_initialization("results")

    user_id = body["user"]["id"]
    sday = body["view"]["state"]["values"]["block_id-sday"]["sday"]["selected_date"]
    eday = body["view"]["state"]["values"]["block_id-eday"]["eday"]["selected_date"]
    selected_options = body["view"]["state"]["values"]["block_id-checkboxes"]["checkboxes"]["selected_options"]

    if sday != None:
        command_option["aggregation_range"] = []
        command_option["aggregation_range"].append(sday.replace("-",""))
    if eday != None:
        command_option["aggregation_range"].append(eday.replace("-",""))

    for i in range(len(selected_options)):
        flag = selected_options[i]["value"]
        if flag == "unregistered_replace":
            command_option[flag] = False
        if flag == "archive":
            command_option[flag] = True

    g.logging.info(command_option)
    target_days, target_player, target_count, command_option = f.common.argument_analysis("", command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "集計中…"
                    }
                }
            ]
        }
    )

    msg = ""
    if starttime and endtime:
        msg = c.results.summary(starttime, endtime, target_player, target_count, command_option)
        f.slack_api.post_text(client, user_id, False, "", msg)

    client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "集計完了"
                    }
                }
            ]
        }
    )
