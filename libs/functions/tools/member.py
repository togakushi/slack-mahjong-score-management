"""
libs/functions/tools/member.py
"""

import logging

import pandas as pd

import libs.global_value as g
from libs.data import modify
from libs.utils import dbutil


def export_data():
    """メンバー情報エクスポート"""
    if g.args.export_data:
        for table in ("member", "alias", "team"):
            csvfile = f"{g.args.export_data}_{table}.csv"

            match table:
                case "member":
                    sql = f"select name, slack_id, flying, reward, abuse, team_id from {table} where id != 0;"
                case _:
                    sql = f"select * from {table};"

            df = pd.read_sql(sql, dbutil.connection(g.cfg.setting.database_file))
            # 整数値を維持
            if "team_id" in df.columns:
                df["team_id"] = df["team_id"].astype("Int64")

            df.to_csv(csvfile, index=False)
            logging.info("export data: %s -> %s", table, csvfile)


def import_data():
    """メンバー情報インポート"""
    if g.args.import_data:
        modify.db_backup()
        conn = dbutil.connection(g.cfg.setting.database_file)
        for table in ("member", "alias", "team"):
            csvfile = f"{g.args.import_data}_{table}.csv"
            conn.execute(f"delete from {table};")

            if table == "member":
                conn.execute(f"delete from sqlite_sequence where name='{table}';")
                conn.execute("insert into member (id, name) values (0, ?)", (g.cfg.member.guest_name,))

            try:
                pd.read_csv(csvfile).to_sql(
                    table,
                    conn,
                    if_exists="append",
                    index=False,
                )
                logging.info("import data: %s -> %s", csvfile, table)
            except FileNotFoundError:
                logging.info("skip: %s (not found)", csvfile)
            except pd.errors.EmptyDataError:
                logging.info("skip: %s (empty file)", csvfile)

        # aliasテーブルが空の場合は作り直す
        alias_list = conn.execute("select name from alias;").fetchall()
        member_list = conn.execute("select name, name from member where id != 0;").fetchall()
        if not alias_list:
            logging.warning("create new alias table")
            for name in member_list:
                conn.execute("insert into alias(name, member) values (?,?);", name)

        conn.commit()
        conn.close()
