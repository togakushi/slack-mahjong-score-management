#!/usr/bin/env python3
import os, sys
import configparser
import sqlite3

import lib.function as f
from lib.function import global_value as g

f.configure.read_memberlist()

if g.args.member:
    g.memberfile = g.args.member
else:
    g.memberfile = g.config["member"].get("filename", "member.ini")

try:
    g.player_list = configparser.ConfigParser()
    g.player_list.read(g.memberfile, encoding="utf-8")
    g.logging.info(f"configload: {g.memberfile} -> {g.player_list.sections()}")
except:
    sys.exit(f"{g.memberfile}: file not found")


if os.path.exists(g.database_file):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)

    # 登録済みメンバーを削除
    resultdb.execute("delete from member where id > 0")
    resultdb.execute("delete from alias")
    resultdb.execute("update sqlite_sequence set seq=0 where name='member'")

    # データインポート
    for player in g.player_list.sections():
        if player == "DEFAULT":
            continue

        alias = g.player_list[player]["alias"].split(",")
        resultdb.execute(f"insert into member(name) values (?)", (player,))
        for aliasname in alias:
            resultdb.execute(f"insert into alias(name, member) values (?,?)", (aliasname, player))

    resultdb.commit()
    resultdb.close()
else:
    sys.exit(f"No such file: {g.database_file}")
