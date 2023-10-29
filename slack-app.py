#!/usr/bin/env python3
import os

from slack_bolt.adapter.socket_mode import SocketModeHandler

import lib.command as c
import lib.event as e
import lib.function as f
from lib.function import global_value as g


# イベントAPI
@g.app.event("message")
def handle_message_events(client, body):
    """
    postされた素点合計が配給原点と同じかチェックする
    """

    data = body["event"]
    channel_id = data["channel"]
    if body["authorizations"][0]["is_bot"]:
        bot_id = body["authorizations"][0]["user_id"]
    else:
        bot_id = None

    if "subtype" in data:
        if data["subtype"] == "message_deleted":
            return
        if data["subtype"] == "message_changed":
            data = body["event"]["message"]

    msg = c.search.pattern(data["text"])
    if msg:
        # リアクションデータ取得
        res = client.reactions_get(
            channel = channel_id,
            timestamp = data["ts"],
        )

        reaction = None
        if "reactions" in res["message"]:
            reaction = res["message"]["reactions"]
            for i in range(len(reaction)):
                if bot_id in reaction[i]["users"]:
                    break
            else:
                reaction = None

        pointsum = g.config["mahjong"].getint("point", 250) * 4
        score = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

        if score == pointsum:
            if reaction:
                client.reactions_remove(
                    channel = channel_id,
                    name = g.reaction_ng,
                    timestamp = data["ts"],
                )
            client.reactions_add(
                channel = channel_id,
                name = g.reaction_ok,
                timestamp = data["ts"],
            )
        else:
            msg = f.message.invalid_score(data["user"], score, pointsum)
            f.slack_api.post_message(client, channel_id, msg, data["ts"])
            if reaction:
                client.reactions_remove(
                    channel = channel_id,
                    name = g.reaction_ok,
                    timestamp = data["ts"],
                )
            client.reactions_add(
                channel = channel_id,
                name = g.reaction_ng,
                timestamp = data["ts"],
            )


@g.app.event("app_home_opened")
def handle_home_events(client, event):
    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    g.logging.info(f"[home_opened] {g.app_var}")

    result = client.views_publish(
        user_id = g.app_var["user_id"],
        view = e.BuildMainMenu(),
    )

    g.logging.trace(result)


if __name__ == "__main__":
    f.configure.parameter_load()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
