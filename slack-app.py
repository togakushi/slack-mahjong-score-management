#!/usr/bin/env python3

import logging
import sys
import os
import re

from slack_bolt.adapter.socket_mode import SocketModeHandler

from function import global_value as g
from function import common
from function import message
from function import slack_api
from goburei import member
from goburei import search
from goburei import results
from goburei import record
from goburei import graph

logging.basicConfig(level = g.logging_level)


# イベントAPI
@g.app.message(re.compile(r"御無礼"))
def handle_goburei_check_evnts(client, body):
    """
    postされた素点合計が10万点になっているかチェックする
    """

    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    msg = search.pattern(body["event"]["text"])
    if msg:
        score = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])
        if not score == 1000:
            msg = message.invalid_score(user_id, score)
            slack_api.post_message(client, channel_id, msg)


@g.app.command("/goburei")
def goburei_command(ack, body, client):
    ack()
    user_id = body["user_id"]

    command_option = {
        "default_action": ["今月"],
         "name_replace": True, # 表記ブレ修正
        "guest_rename": True, # 未登録をゲストに置き換え
        "guest_skip": True, # 2ゲスト戦除外(サマリ用)
        "guest_skip2": False, # 2ゲスト戦除外(個人成績用)
        "results": False, # 戦績表示
        "recursion": True,
    }

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]

        if subcom.lower() in ("results", "details", "成績"):
            logging.info(f"[subcommand({subcom})] {command_option} {argument}")
            results.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in ("record", "記録", "結果"):
            title, msg = record.getdata(name_replace = True, guest_skip = True)
            slack_api.post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("graph", "グラフ"):
            command_option["default_action"] = ["当日"]
            logging.info(f"[subcommand({subcom})] {command_option} {argument}")
            graph.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in ("member", "userlist", "メンバー", "リスト"):
            title, msg = member.list()
            slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("add", "追加"):
            msg = member.Append(argument)
            slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("del", "削除"):
            msg = member.Remove(argument)
            slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("load"):
            g.player_list = member.configload(sys.argv[1])
            slack_api.post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in ("save"):
            member.configsave(g.player_list, sys.argv[1])
            slack_api.post_message(client, user_id, f"メンバーリストを保存しました。")
            return

    slack_api.post_message(client, user_id, message.help(body["command"]))


@g.app.event("message")
def handle_message_events():
    pass


@g.app.event("app_home_opened")
def handle_home_events():
    pass


if __name__ == "__main__":
    g.player_list = member.configload(g.args.member)
    g.config = common.configload(g.args.config)

    logging.info(f"member: {g.player_list.sections()}")
    logging.info(f"config: {g.config.sections()}")

    print(g.config.getboolean("status", "display"))
    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
