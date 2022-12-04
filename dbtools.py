#!/usr/bin/env python3
import argparse
import sqlite3

import database as db
import function as f
from function import global_value as g


f.common.parameter_load()
conn = sqlite3.connect(g.dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
cur = conn.cursor()

if g.args.init:
    db.initialization.create_table(cur)
    conn.commit()

if g.args.csvimport:
    db.initialization.csvimport(cur, g.args.infile)
    conn.commit()

if g.args.export:
    command_option = f.command_option_initialization("record") # 一旦recordに合わせる
    g.logging.info(f"[dbtools] {command_option}")
    exportfile = f.score.csv_export(["先月"], command_option)

db.common.select_table(cur)

conn.close()