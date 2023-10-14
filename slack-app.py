#!/usr/bin/env python3
import os
import re

from slack_bolt.adapter.socket_mode import SocketModeHandler

import lib.event
import command as c
import lib.function as f
from lib.function import global_value as g

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


if __name__ == "__main__":
    f.configure.parameter_load()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
