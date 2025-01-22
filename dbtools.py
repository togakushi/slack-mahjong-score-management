#!/usr/bin/env python3
import os
import sqlite3
import sys

import pandas as pd
from slack_bolt import App
from slack_sdk import WebClient

import global_value as g
from lib import database as d
from lib.function import configuration

if __name__ == "__main__":
    configuration.setup()

    # 突合
    if g.args.compar:
        try:
            g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        except Exception:
            sys.exit()

        count, _, fts = d.comparison.score_comparison()
        if fts:
            count["remark"] = d.comparison.remarks_comparison(fts)

        print(f">>> {count=}")

    # エクスポート
    if g.args.export_data:
        for table in ("member", "alias", "team"):
            csvfile = f"{g.args.export_data}_{table}.csv"
            df = pd.read_sql(
                f"select * from {table};",
                sqlite3.connect(g.cfg.db.database_file),
            )
            # 整数値を維持
            if "team_id" in df.columns:
                df["team_id"] = df["team_id"].astype("Int64")

            df.to_csv(csvfile, index=False)
            print(f">>> export data: {table} -> {csvfile}")

    # インポート
    if g.args.import_data:
        d.common.db_backup()
        conn = sqlite3.connect(g.cfg.db.database_file)
        for table in ("member", "alias", "team"):
            conn.execute(f"delete from {table};")
            csvfile = f"{g.args.import_data}_{table}.csv"
            try:
                pd.read_csv(csvfile).to_sql(
                    table,
                    conn,
                    if_exists="append",
                    index=False,
                )
                print(f">>> import data: {csvfile} -> {table}")
            except FileNotFoundError:
                print(f">>> skip: {csvfile} (not found)")
            except pd.errors.EmptyDataError:
                print(f">>> skip: {csvfile} (empty file)")

        conn.commit()
        conn.close()
