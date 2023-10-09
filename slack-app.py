#!/usr/bin/env python3
import os
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from slack_bolt.adapter.socket_mode import SocketModeHandler

import command as c
import function as f
from function import global_value as g

keyword = g.config["search"].get("keyword", "麻雀成績")

# イベントAPI
@g.app.message(re.compile(rf"{keyword}"))
def handle_score_check_evnts(client, body):
    """
    postされた素点合計が配給原点と同じかチェックする
    """

    g.logging.trace(body["event"])
    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    ts = body["event"]["ts"]
    msg = c.search.pattern(body["event"]["text"])

    if msg:
        pointsum = g.config["mahjong"].getint("point", 250) * 4
        score = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])
        if not score == pointsum:
            msg = f.message.invalid_score(user_id, score, pointsum)
            f.slack_api.post_message(client, channel_id, msg, ts)


@g.app.event("message")
def handle_message_events():
    pass


@g.app.event("app_home_opened")
def handle_home_events(client, event):
    user_id = event["user"]

    initial_date = (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d")
    result = client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
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
                        "text": "検索開始日"
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
                        "text": "検索終了日"
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
                                "text": "御無礼サーチ"
                            },
                            "value": "gobrei_search",
                            "action_id": "actionId-0"
                        }
                    ]
                }
            ]
        }
    )

    g.logging.trace(result)

@g.app.action("actionId-0")
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

    msg = ""
    if starttime and endtime:
        msg = c.results.summary(starttime, endtime, target_player, target_count, command_option)
        if len(msg.strip().splitlines()) >= 2:
            msg = "```" + msg + "```"

    client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "block_id": "PlainText",
                    "text": {
                        "type": "mrkdwn",
                        "text": msg
                    }
                }
            ]
        }
    )


if __name__ == "__main__":
    f.configure.parameter_load()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
