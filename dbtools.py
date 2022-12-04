#!/usr/bin/env python3
import argparse
import sqlite3

import function as f
import database as db
from function import global_value as g


f.common.parameter_load()
conn = sqlite3.connect(g.args.database)
cur = conn.cursor()

if g.args.init:
    db.initialization.create_tb(cur)

if g.args.csv_import:
    db.initialization.csv_import(cur, g.args.infile)

if g.args.export:
    command_option = f.command_option_initialization("record") # 一旦recordに合わせる
    g.logging.info(f"[dbtools] {command_option}")
    exportfile = f.score.csv_export(["先月"], command_option)

conn.commit()
conn.close()