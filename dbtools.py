#!/usr/bin/env python3
import os
import sqlite3

import lib.function as f
import lib.database as d
from lib.function import global_value as g


def name_normalization(player_list, name):
    if f.HIRA2KANA(name) in player_list:
        return(player_list[f.HIRA2KANA(name)])
    if f.KANA2HIRA(name) in player_list:
        return(player_list[f.KANA2HIRA(name)])

    return(name)


# ---
f.configure.parameter_load()
command_option = f.configure.command_option_initialization("record")
command_option["unregistered_replace"] = False # ゲスト無効
resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
resultdb.row_factory = sqlite3.Row
cur = resultdb.cursor()

# メンバーリスト
if os.path.exists(g.database_file):
    rows = cur.execute("select name, member from alias;")

    player_list = {}
    for row in rows.fetchall():
        if not row["member"] in player_list:
            player_list[row["member"]] = row["member"]
        if not row["name"] in player_list:
            player_list[row["name"]] = row["member"]

# --- data
slack_data = d.slack_search(command_option)
fts = list(slack_data.keys())[0]
db_data = d.databese_search(cur, fts.split(".")[0] + ".0")

# --- 突合
mismatch, missing, delete = d.data_comparison(cur, slack_data, db_data, command_option)
print(f">>> mismatch:{mismatch}, missing:{missing}, delete:{delete}")

resultdb.commit()
resultdb.close()
