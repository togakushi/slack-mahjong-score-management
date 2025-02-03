#!/usr/bin/env python3
import os
import sqlite3
import sys

import pandas as pd
from slack_bolt import App
from slack_sdk import WebClient

import global_value as g
from lib import command as c
from lib import database as d
from lib.function import configuration

if __name__ == "__main__":
    configuration.setup()

    # 突合
    if g.args.compar:
        try:
            g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.bot_id = g.app.client.auth_test()["user_id"]
            c.member.read_memberslist()
        except Exception as err:
            sys.exit(err)

        count, _ = d.comparison.data_comparison()
        print(f">>> {count=}")

    # エクスポート
    if g.args.export_data:
        for table in ("member", "alias", "team"):
            csvfile = f"{g.args.export_data}_{table}.csv"

            match table:
                case "member":
                    sql = f"select name, slack_id, flying, reward, abuse, team_id from {table} where id != 0;"
                case _:
                    sql = f"select * from {table};"

            df = pd.read_sql(sql, sqlite3.connect(g.cfg.db.database_file))
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
            csvfile = f"{g.args.import_data}_{table}.csv"
            conn.execute(f"delete from {table};")

            if table == "member":
                conn.execute(f"delete from sqlite_sequence where name='{table}';")
                conn.execute("insert into member (id, name) values (0, ?)", (g.prm.guest_name,))

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

        # aliasテーブルが空の場合は作り直す
        alias_list = conn.execute("select name from alias;").fetchall()
        member_list = conn.execute("select name, name from member where id != 0;").fetchall()
        if not alias_list:
            print(">>> create new alias table")
            for name in member_list:
                conn.execute("insert into alias(name, member) values (?,?);", name)

        conn.commit()
        conn.close()
