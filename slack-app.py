#!/usr/bin/env python3

import logging
import sys
import os
import re

from slack_bolt.adapter.socket_mode import SocketModeHandler

from function import global_value as g
from function import common
from function import error
from function import slack_api
from goburei import member
from goburei import search
from goburei import results
from goburei import record
from goburei import details
from goburei import graph

logging.basicConfig(level = logging.ERROR)

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
            msg = error.invalid_score(user_id, score)
            slack_api.post_message(client, channel_id, msg)


@g.app.command("/goburei")
def goburei_command(ack, body, client):
    ack()
    user_id = body["user_id"]
    msg = ""

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]
        details_flag = False

        if subcom.lower() in ("results", "details", "成績", "個人"):
            for i in argument:
                if member.ExsistPlayer(i):
                    details_flag = True
            if details_flag:
                msg = details.getdata(argument)
                slack_api.post_message(client, user_id, msg)
            else:
                title, msg = results.getdata(argument, name_replace = True, guest_skip = True)
                slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("member", "userlist", "メンバー", "リスト"):
            title, msg = member.list()
            slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("allresults", "全成績"):
            title, msg = results.getdata(name_replace = False, guest_skip = False)
            slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("record", "記録", "結果"):
            title, msg = record.getdata(name_replace = True, guest_skip = True)
            slack_api.post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("allrecord", "全記録", "全結果"):
            title, msg = record.getdata(name_replace = False, guest_skip = False)
            slack_api.post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("graph", "グラフ"):
            graph.slackpost(client, user_id, argument)
            return

        if subcom.lower() in ("load"):
            g.player_list = member.configload(sys.argv[1])
            slack_api.post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in ("save"):
            member.configsave(g.player_list, sys.argv[1])
            slack_api.post_message(client, user_id, f"メンバーリストを保存しました。")
            return

        if subcom.lower() in ("add", "追加"):
            msg = member.Append(body["text"].split())
            slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("del", "削除"):
            msg = member.Remove(body["text"].split())
            slack_api.post_message(client, user_id, msg)
            return

    msg = "使い方：\n"
    msg += "`{} {}` {}\n".format(body["command"], "help", "このメッセージ")
    msg += "`{} {}` {}\n".format(body["command"], "results", "今月の成績")
    msg += "`{} {}` {}\n".format(body["command"], "record", "張り付け用集計済みデータ出力")
    msg += "`{} {}` {}\n".format(body["command"], "allrecord", "集計済み全データ出力(名前ブレ修正なし)")
    msg += "`{} {}` {}\n".format(body["command"], "graph", "ポイント推移グラフを表示")
    msg += "`{} {} <名前>` {}\n".format(body["command"], "details", "2ゲスト戦含む個人成績出力")
    msg += "`{} {}` {}\n".format(body["command"], "member | userlist", "登録されているメンバー")
    msg += "`{} {}` {}\n".format(body["command"], "add", "メンバーの追加")
    msg += "`{} {}` {}\n".format(body["command"], "del", "メンバーの削除")
    msg += "`{} {}` {}\n".format(body["command"], "load", "メンバーリストの再読み込み")
    msg += "`{} {}` {}\n".format(body["command"], "save", "メンバーリストの保存")

    slack_api.post_message(client, user_id, msg)


@g.app.event("message")
def handle_message_events():
    pass


@g.app.event("app_home_opened")
def handle_home_events():
    pass


if __name__ == "__main__":
    g.player_list = member.configload(sys.argv[1])
    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
