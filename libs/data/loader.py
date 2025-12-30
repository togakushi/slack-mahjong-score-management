"""
libs/data/loader.py
"""

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, cast

import pandas as pd

import libs.global_value as g
from libs.utils import dbutil

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime as ExtDt


def read_data(keyword: str) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        keyword (str): SQL選択キーワード

    Returns:
        pd.DataFrame: 集計結果
    """

    if "starttime" in g.params:
        g.params.update({"starttime": cast("ExtDt", g.params["starttime"]).format("sql")})
    if "endtime" in g.params:
        g.params.update({"endtime": cast("ExtDt", g.params["endtime"]).format("sql")})

    sql = query_modification(dbutil.query(keyword))
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
    except pd.errors.DatabaseError:
        logging.critical("SQL: %s, DATABASE: %s", keyword, g.cfg.setting.database_file)
        logging.critical("params=%s", g.params)
        logging.critical("query: %s", named_query(sql))

    if g.args.verbose & 0x02:
        print("=" * 80)
        print(df.to_string())

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
        g.params.update({"unregistered_replace": False})
        g.params.update({"guest_skip": True})
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

    # 集計対象ルール
    rule_list: list = []
    g.params["mode"] = g.params.get("mode", 4)
    if target_mode := g.params.get("target_mode"):
        g.params["mode"] = target_mode
        rule_list.extend(g.cfg.rule.get_version(g.params["mode"], True))
    if g.params.get("mixed"):
        rule_list.extend(g.cfg.rule.get_version(g.params["mode"], False))
    if (rule_version := g.params.get("rule_version")) and g.cfg.rule.to_dict(rule_version):
        rule_list.append(rule_version)
    if not rule_list:
        rule_list = list(g.cfg.rule.keyword_mapping.values())
    g.params["rule_set"] = {f"rule_{idx}": name for idx, name in enumerate(set(rule_list))}
    sql = sql.replace("<<rule_list>>", ":" + ", :".join(g.params["rule_set"]))

    # スコア入力元識別子別集計
    if g.params.get("separate"):
        sql = sql.replace("--[separate] ", "")

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
        sql = sql.replace("and my.playtime between", "-- and my.playtime between")

    # プレイヤーリスト
    if g.params.get("player_name"):
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace("<<player_list>>", ":" + ", :".join(g.params["player_list"]))
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
            sql = sql.replace("<<Calculation Formula>>", "(row_number() over (order by total_count desc) - 1) / :interval")
    if g.params.get("kind") is not None:
        if g.params.get("kind") == "yakuman":
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
