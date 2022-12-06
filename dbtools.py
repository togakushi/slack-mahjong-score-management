#!/usr/bin/env python3
import argparse
import sqlite3

import database as db
import function as f
from function import global_value as g

f.common.parameter_load()
command_option = f.command_option_initialization("record") # 一旦recordに合わせる

channel = g.config["database"].get("notification", None)

conn = sqlite3.connect(g.dbfile, detect_types = sqlite3.PARSE_DECLTYPES)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

if g.args.init:
    db.initialization.create_table(cur)
    conn.commit()

if g.args.csvimport:
    count = db.initialization.csv_import(cur, g.args.csvimport)
    conn.commit()
    print(f"import : {count}")

if g.args.export:
    g.logging.info(f"[dbtools] {command_option}")
    exportfile = f.score.csv_export(["先月"], command_option)

db.common.select_table(cur, command_option)

conn.close()