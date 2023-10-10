from datetime import datetime

from dateutil.relativedelta import relativedelta

import command as c
import function as f
from function import global_value as g


@g.app.action("actionId-summary_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

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
                        "text": "集計期間"
                    }
                },
                {
                    "type": "input",
                    "block_id": "block_id-sday",
                    "element": {
                        "type": "datepicker",
                        "initial_date": initial_date,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "sday"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "開始日"
                    },
                },
                {
                    "type": "input",
                    "block_id": "block_id-eday",
                    "element": {
                        "type": "datepicker",
                        "initial_date": initial_date,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "eday"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "終了日"
                    }
                },
                {
                    "type": "input",
                    "block_id": "block_id-checkboxes",
                    "element": {
                        "type": "checkboxes",
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "ゲスト無効"
                                },
                                "value": "unregistered_replace"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "アーカイブ"
                                },
                                "value": "archive"
                            },
                        ],
                        "initial_options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "ゲスト無効"
                                },
                                "value": "unregistered_replace"
                            }
                        ],
                        "action_id": "checkboxes"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "検索オプション"
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
                            "value": "gobrei_search",
                            "action_id": "actionId-search"
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
