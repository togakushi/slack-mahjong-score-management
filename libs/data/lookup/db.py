"""
lib/data/lookup/db.py
"""

import sqlite3
from contextlib import closing
from datetime import datetime

import pandas as pd

import libs.global_value as g
from libs.data import loader


def get_member_id(name: str | None = None) -> dict:
    """メンバーのIDを返す

    Args:
        name (str | None, optional): 指定メンバーのみ. Defaults to None.

    Returns:
        dict: メンバー名とIDのペア
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file)
    rows = resultdb.execute("select name, id from member;")
    id_list = dict(rows.fetchall())
    resultdb.close()

    if name in id_list:
        return {name: id_list[name]}
    return id_list


def member_info(name: str) -> dict:
    """指定メンバーの記録情報を返す

    Args:
        name (str): 対象メンバー

    Returns:
        dict: 記録情報
    """

    sql = """
        select
            count() as game_count,
            min(ts) as first_game,
            max(ts) as last_game,
            max(rpoint) as max_rpoint,
            min(rpoint) as min_rpoint
        from
            --[individual] individual_results as results
            --[team] team_results as results
        where
            rule_version = ?
            and name = ?
    """

    sql = loader.query_modification(sql)
    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(sql, (g.cfg.mahjong.rule_version, name))
    ret = dict(rows.fetchone())
    resultdb.close()
    return ret


def rule_version_range() -> dict:
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule: dict = {}
    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        ret = cur.execute(
            """
            select
                rule_version,
                strftime("%Y/%m/%d %H:%M:%S", min(playtime)) as min,
                strftime("%Y/%m/%d %H:%M:%S", max(playtime)) as max
            from
                result
            group by
                rule_version
            """
        )

        for version, first_time, last_time in ret.fetchall():
            rule[version] = {
                "first_time": first_time,
                "last_time": last_time,
            }

    return rule


def regulation_list(word_type: int = 0) -> list:
    """登録済みワードリストを取得する

    Args:
        word_type (int, optional): 取得するタイプ. Defaults to 0.

    Returns:
        list: 取得結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        ret = cur.execute(
            """
            select
                word,
                ex_point
            from
                words
            where
                type=?
            """, (word_type,)
        ).fetchall()

    return ret


def exsist_record(ts: str) -> dict:
    """記録されているゲーム結果を返す

    Args:
        ts (str): 検索するタイムスタンプ

    Returns:
        dict: 検索結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        row = cur.execute("select * from result where ts=?", (ts,)).fetchone()

    if row:
        return dict(row)
    return {}


def first_record() -> datetime:
    """最初のゲーム記録時間を返す

    Returns:
        datetime: 最初のゲーム記録時間
    """

    ret = datetime.now()
    try:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as resultdb:
            table_count = resultdb.execute(
                "select count() from sqlite_master where type='view' and name='game_results';",
            ).fetchall()[0][0]

            if table_count:
                record = resultdb.execute(
                    "select min(playtime) from game_results where rule_version=?;",
                    (g.params.get("rule_version", g.cfg.mahjong.rule_version), )
                ).fetchall()[0][0]
                if record:
                    ret = datetime.fromisoformat(record)
    except AttributeError:
        ret = datetime.now()

    return ret


def get_results_list(name: str, rule_version: str = "") -> pd.DataFrame:
    """段位集計用順位リスト生成

    Args:
        name (str): 集計対象メンバー名
        rule_version (str, optional): 集計ルールバージョン. Defaults to 空欄.

    Returns:
        pd.DataFrame: 順位, 素点
    """

    ret_data = pd.read_sql(
        g.sql["SELECT_ALL_RESULTS"],
        sqlite3.connect(g.cfg.db.database_file),
        params={
            "rule_version": rule_version if rule_version else g.cfg.mahjong.rule_version,
            "player_name": name,
        }
    )

    return ret_data
