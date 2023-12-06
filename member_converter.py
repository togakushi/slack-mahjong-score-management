#!/usr/bin/env python3
import os, sys
import sqlite3

import lib.function as f
from lib.function import global_value as g

f.configure.parameter_load()

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
