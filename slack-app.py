#!/usr/bin/env python3
import sys
import os
import re

from slack_bolt.adapter.socket_mode import SocketModeHandler

import function as f
import command as c
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


@g.app.command("/goburei")
def goburei_command(ack, body, client):
    ack()
    user_id = body["user_id"]

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]

        if subcom.lower() in ("results", "details", "成績"):
            command_option = f.command_option_initialization("results")
            g.logging.info(f"[subcommand({subcom})] {command_option} {argument}")
            c.results.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in ("record", "記録", "結果"):
            command_option = f.command_option_initialization("record")
            title, msg = c.record.getdata(playername_replace = True, guest_skip = True)
            f.slack_api.post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("graph", "グラフ"):
            command_option = f.command_option_initialization("graph")
            g.logging.info(f"[subcommand({subcom})] {command_option} {argument}")
            c.graph.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in ("member", "userlist", "メンバー", "リスト"):
            title, msg = c.member.list()
            f.slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("add", "追加"):
            msg = c.member.Append(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("del", "削除"):
            msg = c.member.Remove(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("load"):
            g.player_list = f.options.configload(g.args.member)
            f.slack_api.post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in ("save"):
            f.options.configsave(g.player_list, g.args.member)
            f.slack_api.post_message(client, user_id, f"メンバーリストを保存しました。")
            return

    slack_api.post_message(client, user_id, f.message.help(body["command"]))


@g.app.event("message")
def handle_message_events():
    pass


@g.app.event("app_home_opened")
def handle_home_events():
    pass


if __name__ == "__main__":
    g.player_list = f.common.configload(g.args.member)
    g.config = f.common.configload(g.args.config)
    g.guest_name = g.config["search"].get("guest_name", "ゲスト")

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
