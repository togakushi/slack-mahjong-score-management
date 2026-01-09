"""
libs/data/loader.py
"""

import logging
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

import pandas as pd

import libs.global_value as g
from cls.timekit import Format
from libs.utils import dbutil

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime as ExtDt


def execute(sql: str) -> list[dict[str, Any]]:
    """クエリ実行

    Args:
        sql (str): 実行クエリ

    Returns:
        list[dict[str, Any]]: 実行結果
    """

    ret: list[dict[str, Any]] = []
    sql = dbutil.query_modification(sql)

    if g.args.verbose & 0x01:
        print(f">>> {g.params=}")
        print(f">>> SQL -> {g.cfg.setting.database_file}\n{named_query(sql)}")

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        try:
            rows = conn.execute(sql, g.params)
        except sqlite3.OperationalError as err:
            logging.error("OperationalError: %s", err)
            logging.error("params=%s", g.params)
            logging.error("query: %s", named_query(sql))
            return ret

        for row in rows.fetchall():
            ret.append(dict(row))

        if g.args.verbose & 0x02:
            print("=" * 80)
            print(ret)

    return ret


def read_data(keyword: str) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        keyword (str): SQL選択キーワード

    Returns:
        pd.DataFrame: 集計結果
    """

    sql = dbutil.query_modification(dbutil.query(keyword))

    if starttime := g.params.get("starttime"):
        g.params.update({"starttime": cast("ExtDt", starttime).format(Format.SQL)})
    if endtime := g.params.get("endtime"):
        g.params.update({"endtime": cast("ExtDt", endtime).format(Format.SQL)})

    if g.args.verbose & 0x01:
        print(f">>> {g.params=}")
        print(f">>> SQL: {keyword} -> {g.cfg.setting.database_file}\n{named_query(sql)}")

    try:
        df = pd.read_sql(
            sql=sql,
            con=dbutil.connection(g.cfg.setting.database_file),
            params={
                **cast(dict, g.params),
                **g.params.get("rule_set", {}),
                **g.params.get("player_list", {}),
                **g.params.get("competition_list", {}),
            },
        )
    except pd.errors.DatabaseError as err:
        logging.error("DatabaseError: %s", err)
        logging.error("SQL: %s, DATABASE: %s", keyword, g.cfg.setting.database_file)
        logging.error("params=%s", g.params)
        logging.error("query: %s", named_query(sql))

    if g.args.verbose & 0x02:
        print("=" * 80)
        print(df.to_string())

    return df


def named_query(query: str) -> str:
    """クエリにパラメータをバインドして返す

    Args:
        query (str): SQL

    Returns:
        str: バインド済みSQL
    """

    params: dict = cast(dict, g.params.copy())
    params.update(
        **g.params.get("rule_set", {}),
        **g.params.get("player_list", {}),
        **g.params.get("competition_list", {}),
    )

    for k, v in params.items():
        if isinstance(v, datetime):
            params[k] = v.strftime("%Y-%m-%d %H:%M:%S")

    return re.sub(r":(\w+)", lambda m: repr(params.get(m.group(1), m.group(0))), query)
