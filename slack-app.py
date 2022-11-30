#!/usr/bin/env python3
import os
import re
import sys

from slack_bolt.adapter.socket_mode import SocketModeHandler

import command as c
import function as f
from function import global_value as g


# イベントAPI
@g.app.message(re.compile(r"御無礼"))
def handle_goburei_check_evnts(client, body):
    """
    postされた素点合計が10万点になっているかチェックする
    """

    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    msg = c.search.pattern(body["event"]["text"])
    if msg:
        score = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])
        if not score == 1000:
            msg = f.message.invalid_score(user_id, score)
            f.slack_api.post_message(client, channel_id, msg)


@g.app.event("message")
def handle_message_events():
    pass


@g.app.event("app_home_opened")
def handle_home_events():
    pass


if __name__ == "__main__":
    f.common.parameter_load()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
