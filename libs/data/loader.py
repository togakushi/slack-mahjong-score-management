"""
libs/data/loader.py
"""

import logging
import re
import sqlite3
import textwrap
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

import pandas as pd

import libs.global_value as g
from cls.timekit import Format
from libs.utils import dbutil

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime as ExtDt


def execute(sql: str, params: dict = {}) -> list[dict[str, Any]]:
    """クエリ実行

    Args:
        sql (str): 実行クエリ
        params (dict): プレースホルダ

    Returns:
        list[dict[str, Any]]: 実行結果
    """

    ret: list[dict[str, Any]] = []
    sql = dbutil.query_modification(sql)

    params.update(
        **params.get("rule_set", {}),
        **params.get("player_list", {}),
        **params.get("competition_list", {}),
    )

    if g.args.verbose & 0x01:
        print(f">>> {params=}")
        print(f">>> SQL -> {g.cfg.setting.database_file}\n{named_query(sql, params)}")

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        try:
            rows = conn.execute(sql, params)
            if conn.total_changes:
                conn.commit()
        except sqlite3.OperationalError as err:
            logging.error("OperationalError: %s", err)
            logging.error("params=%s", params)
            logging.error("query: %s", named_query(sql, params))
            return ret

        for row in rows.fetchall():
            ret.append(dict(row))

        if g.args.verbose & 0x02:
            print("=" * 80)
            print(ret)

    return ret


def read_data(keyword: str, params: dict = {}) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        keyword (str): SQL選択キーワード
        params (dict): プレースホルダ

    Returns:
        pd.DataFrame: 集計結果
    """

    if not params:
        params = cast(dict, g.params)

    sql = dbutil.query_modification(dbutil.query(keyword))

    if starttime := params.get("starttime"):
        params.update({"starttime": cast("ExtDt", starttime).format(Format.SQL)})
    if endtime := params.get("endtime"):
        params.update({"endtime": cast("ExtDt", endtime).format(Format.SQL)})

    if g.args.verbose & 0x01:
        print(f">>> {params=}")
        print(f">>> SQL: {keyword} -> {g.cfg.setting.database_file}\n{named_query(sql, cast(dict, g.params))}")

    try:
        df = pd.read_sql(
            sql=sql,
            con=dbutil.connection(g.cfg.setting.database_file),
            params={
                **params,
                **g.params.get("rule_set", {}),
                **g.params.get("player_list", {}),
                **g.params.get("competition_list", {}),
            },
        )
    except pd.errors.DatabaseError as err:
        logging.error("DatabaseError: %s", err)
        logging.error("SQL: %s, DATABASE: %s", keyword, g.cfg.setting.database_file)
        logging.error("params=%s", params)
        logging.error("query: %s", named_query(sql, params))

    if g.args.verbose & 0x02:
        print("=" * 80)
        print(df.to_string())

    return df


def named_query(query: str, params: dict) -> str:
    """クエリにパラメータをバインドして返す

    Args:
        query (str): SQL
        params (dict): プレースホルダ

    Returns:
        str: バインド済みSQL
    """

    params.update(
        **g.params.get("rule_set", {}),
        **g.params.get("player_list", {}),
        **g.params.get("competition_list", {}),
    )

    for k, v in params.items():
        if isinstance(v, datetime):
            params[k] = v.strftime("%Y-%m-%d %H:%M:%S")

    return textwrap.dedent(re.sub(r":(\w+)", lambda m: repr(params.get(m.group(1), m.group(0))), query)).strip()
