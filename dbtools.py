#!/usr/bin/env python3
import os
import sqlite3

import lib.function as f
import lib.database as d
from lib.function import global_value as g


# ---
f.configure.read_memberlist()
command_option = f.configure.command_option_initialization("record")
command_option["unregistered_replace"] = False # ゲスト無効

resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
resultdb.row_factory = sqlite3.Row
cur = resultdb.cursor()

# --- 比較データ取得
slack_data = d.slack_search(command_option)
fts = list(slack_data.keys())[0]
db_data = d.databese_search(cur, fts.split(".")[0] + ".0")

# --- 突合
count, msg = d.data_comparison(cur, slack_data, db_data, command_option)
print(f">>> mismatch:{count['mismatch']}, missing:{count['missing']}, delete:{count['delete']}")

resultdb.commit()
resultdb.close()
