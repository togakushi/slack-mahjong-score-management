"""
lib/data/lookup/db.py
"""

from contextlib import closing
from datetime import datetime

import pandas as pd

import libs.global_value as g
from cls.score import GameResult
from cls.types import TeamDataDict
from libs.data import loader
from libs.utils import dbutil


def get_member_id(name: str | None = None) -> dict:
    """メンバーのIDを返す

    Args:
        name (str | None, optional): 指定メンバーのみ. Defaults to None.

    Returns:
        dict: メンバー名とIDのペア
    """

    with closing(dbutil.get_connection()) as conn:
        rows = conn.execute("select name, id from member;")
        id_list = dict(rows.fetchall())

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

    ret: dict = {}
    sql = loader.query_modification("""
        select
            count() as game_count,
            min(ts) as first_game,
            max(ts) as last_game,
            max(rpoint) as rpoint_max,
            min(rpoint) as rpoint_min
        from
            individual_results as results
        where
            rule_version = ?
            --[individual] and name = ?
            --[team] and team = ?
    """)

    with closing(dbutil.get_connection()) as conn:
        rows = conn.execute(sql, (g.cfg.mahjong.rule_version, name))
        ret = dict(rows.fetchone())

    return ret


def get_guest() -> str:
    """ゲスト名取得

    Returns:
        str: ゲスト名
    """

    guest_name: str = ""
    with closing(dbutil.get_connection()) as conn:
        rows = conn.execute("select name from member where id=0")
        guest_name = str(rows.fetchone()[0])

    return guest_name


def get_member_list() -> dict[str, str]:
    """メンバー情報取得

    Returns:
        dict[str, str]: 別名, 表示名
    """

    with closing(dbutil.get_connection()) as conn:
        rows = conn.execute("select name, member from alias")
        member_list = dict(rows.fetchall())

    return member_list


def get_team_list() -> list[TeamDataDict]:
    """チーム情報取得

    Returns:
        list[TeamDataDict]: チーム情報
    """

    ret: list[TeamDataDict] = []
    with closing(dbutil.get_connection()) as conn:
        rows = conn.execute(
            """
                select
                    team.id as id,
                    team.name as team,
                    group_concat(member.name) as member
                from
                    team
                left join member on
                    team.id == member.team_id
                group by
                    team.id
            """)

        for row in rows.fetchall():
            ret.append({
                "id": int(row["id"]),
                "team": str(row["team"]),
                "member": str(row["member"]).split(",")
            })

    return ret


def rule_version_range() -> dict:
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule: dict = {}
    with closing(dbutil.get_connection()) as conn:
        ret = conn.execute(
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

    with closing(dbutil.get_connection()) as cur:
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


def exsist_record(ts: str) -> GameResult:
    """記録されているゲーム結果を返す

    Args:
        ts (str): 検索するタイムスタンプ

    Returns:
        GameResult: スコアデータ
    """

    result = GameResult()
    with closing(dbutil.get_connection()) as conn:
        row = conn.execute(g.sql["SELECT_GAME_RESULTS"], {"ts": ts}).fetchone()

    if row:
        result.calc(**dict(row))

    return result


def first_record() -> datetime:
    """最初のゲーム記録時間を返す

    Returns:
        datetime: 最初のゲーム記録時間
    """

    ret = datetime.now()
    try:
        with closing(dbutil.get_connection()) as conn:
            table_count = conn.execute(
                "select count() from sqlite_master where type='view' and name='game_results';",
            ).fetchall()[0][0]

            if table_count:
                record = conn.execute(
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
        sql=g.sql["SELECT_ALL_RESULTS"],
        con=dbutil.get_connection(),
        params={
            "rule_version": rule_version if rule_version else g.cfg.mahjong.rule_version,
            "player_name": name,
        }
    )

    return ret_data
