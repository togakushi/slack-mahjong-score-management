"""
libs/data/loader.py
"""

import logging
import re
from datetime import datetime

import pandas as pd

import libs.global_value as g
from libs.utils import dbutil


def read_data(keyword: str) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        keyword (str): SQL選択キーワード

    Returns:
        pd.DataFrame: 集計結果
    """

    # デバッグ用
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)

    if "starttime" in g.params:
        g.params.update(starttime=g.params["starttime"].format("sql"))
    if "endtime" in g.params:
        g.params.update(endtime=g.params["endtime"].format("sql"))
    if "rule_version" not in g.params:
        g.params.update(rule_version=g.cfg.mahjong.rule_version)

    sql = query_modification(dbutil.query(keyword))
    logging.debug("prm: %s", g.params)
    logging.debug("sql: %s", named_query(sql))

    df = pd.read_sql(
        sql=sql,
        con=dbutil.connection(g.cfg.setting.database_file),
        params=g.params,
    )
    logging.trace(df)  # type: ignore

    return df


def query_modification(sql: str) -> str:
    """クエリをオプションの内容で修正する

    Args:
        sql (str): 修正するクエリ

    Returns:
        str: 修正後のクエリ
    """

    if g.params.get("individual"):  # 個人集計
        sql = sql.replace("--[individual] ", "")
        # ゲスト関連フラグ
        if g.params.get("unregistered_replace"):
            sql = sql.replace("--[unregistered_replace] ", "")
            if g.params.get("guest_skip"):
                sql = sql.replace("--[guest_not_skip] ", "")
            else:
                sql = sql.replace("--[guest_skip] ", "")
        else:
            sql = sql.replace("--[unregistered_not_replace] ", "")
    else:  # チーム集計
        g.params.update(unregistered_replace=False)
        g.params.update(guest_skip=True)
        sql = sql.replace("--[team] ", "")
        if not g.params.get("friendly_fire"):
            sql = sql.replace("--[friendly_fire] ", "")

    # 集約集計
    match g.params.get("collection"):
        case "daily":
            sql = sql.replace("--[collection_daily] ", "")
            sql = sql.replace("--[collection] ", "")
        case "monthly":
            sql = sql.replace("--[collection_monthly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "yearly":
            sql = sql.replace("--[collection_yearly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "all":
            sql = sql.replace("--[collection_all] ", "")
            sql = sql.replace("--[collection] ", "")
        case _:
            sql = sql.replace("--[not_collection] ", "")

    # コメント検索
    if g.params.get("search_word") or g.params.get("group_length"):
        sql = sql.replace("--[group_by] ", "")
    else:
        sql = sql.replace("--[not_group_by] ", "")

    if g.params.get("search_word"):
        sql = sql.replace("--[search_word] ", "")
    else:
        sql = sql.replace("--[not_search_word] ", "")

    if g.params.get("group_length"):
        sql = sql.replace("--[group_length] ", "")
    else:
        sql = sql.replace("--[not_group_length] ", "")
        if g.params.get("search_word"):
            sql = sql.replace("--[comment] ", "")
        else:
            sql = sql.replace("--[not_comment] ", "")

    # 直近N検索用（全範囲取得してから絞る）
    if g.params.get("target_count") != 0:
        sql = sql.replace(
            "and my.playtime between",
            "-- and my.playtime between"
        )

    # プレイヤーリスト
    if g.params.get("player_name"):
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join(g.params["player_list"])
        )
    sql = sql.replace("<<guest_mark>>", g.cfg.setting.guest_mark)

    # フラグの処理
    match g.cfg.aggregate_unit:
        case "M":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 7) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    if g.params.get("interval") is not None:
        if g.params.get("interval") == 0:
            sql = sql.replace("<<Calculation Formula>>", ":interval")
        else:
            sql = sql.replace(
                "<<Calculation Formula>>",
                "(row_number() over (order by total_count desc) - 1) / :interval"
            )
    if g.params.get("kind") is not None:
        if g.params.get("kind") == "grandslam":
            if g.cfg.undefined_word == 0:
                sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 0)")
            else:
                sql = sql.replace("<<where_string>>", "and words.type = 0")
        else:
            match g.cfg.undefined_word:
                case 1:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 1)")
                case 2:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 2)")
                case _:
                    sql = sql.replace("<<where_string>>", "and (words.type = 1 or words.type = 2)")

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    return sql


def named_query(query: str) -> str:
    """クエリにパラメータをバインドして返す

    Args:
        query (str): SQL

    Returns:
        str: バインド済みSQL
    """

    for k, v in g.params.items():
        if isinstance(v, datetime):
            g.params[k] = v.strftime("%Y-%m-%d %H:%M:%S")

    return re.sub(r":(\w+)", lambda m: repr(g.params.get(m.group(1), m.group(0))), query)
