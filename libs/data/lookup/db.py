"""
libs/data/lookup/db.py
"""

import logging
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pandas as pd

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.utils import dbutil

if TYPE_CHECKING:
    from libs.types import MemberDataDict, PlaceholderDict, TeamDataDict


def member_info(params: "PlaceholderDict") -> dict:
    """指定メンバーの記録情報を返す

    Args:
        params (PlaceholderDict): 対象メンバー

    Returns:
        dict: 記録情報
    """

    ret: dict = {}
    sql = dbutil.query_modification(
        """
        select
            count() as game_count,
            min(ts) as first_game,
            max(ts) as last_game,
            max(rpoint) as rpoint_max,
            min(rpoint) as rpoint_min
        from
            individual_results
        where
            mode = :mode
            and rule_version in (<<rule_list>>)
            and playtime between :starttime and :endtime
            --[separate] and source = :source
            --[individual] and name = :player_name
            --[team] and team = :player_name
        """
    )

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        params["starttime"] = cast("ExtDt", params["starttime"]).format("sql")
        params["endtime"] = cast("ExtDt", params["endtime"]).format("sql")
        rows = conn.execute(sql, params)
        ret = dict(rows.fetchone())

    return ret


def get_guest() -> str:
    """ゲスト名取得

    Returns:
        str: ゲスト名
    """

    guest_name: str = ""
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        rows = conn.execute("select name from member where id=0")
        guest_name = str(rows.fetchone()[0])

    return guest_name


def get_member_info() -> list["MemberDataDict"]:
    """メンバー情報取得

    Returns:
        list[MemberDataDict]: メンバー情報
    """

    ret: list["MemberDataDict"] = []
    tmp: "MemberDataDict"

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        rows = conn.execute("select name, id from member where id != 0;")
        id_list = dict(rows.fetchall())

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        rows = conn.execute("select name, member from alias")
        alias_list = dict(rows.fetchall())

    for name, id in id_list.items():
        tmp = {
            "id": id,
            "name": name,
            "alias": [k for k, v in alias_list.items() if v == name],
        }
        ret.append(tmp)

    return ret


def get_team_info() -> list["TeamDataDict"]:
    """チーム情報取得

    Returns:
        list[TeamDataDict]: チーム情報
    """

    ret: list["TeamDataDict"] = []
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
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
            """
        )

        for row in rows.fetchall():
            ret.append({"id": int(row["id"]), "team": str(row["team"]), "member": str(row["member"]).split(",")})

    return ret


def rule_version_range() -> dict:
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule: dict = {}
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
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

    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        ret = cur.execute(
            """
            select
                word,
                ex_point
            from
                words
            where
                type=?
            """,
            (word_type,),
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
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        row = conn.execute(dbutil.query("SELECT_GAME_RESULTS"), {"ts": ts}).fetchone()

    if row:
        result.calc(**dict(row))

    return result


def first_record(rule_list: list[str]) -> ExtDt:
    """最初のゲーム記録時間を返す

    Args:
        rule_list (list[str]): ルールバージョン識別子

    Returns:
        ExtendedDatetime: 最初のゲーム記録時間
    """

    ret = ExtDt()
    g.params["rule_set"] = {f"rule_{idx}": name for idx, name in enumerate(set(rule_list))}

    try:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
            table_count = conn.execute(
                "select count() from sqlite_master where type='view' and name='game_results';",
            ).fetchall()[0][0]

            if table_count:
                sql = dbutil.query_modification("select min(playtime) from game_results where rule_version in (<<rule_list>>);")
                record = conn.execute(sql, g.params["rule_set"]).fetchall()[0][0]
                if record:
                    ret = ExtDt(str(record))
    except AttributeError:
        ret = ExtDt()

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
        sql=dbutil.query("SELECT_ALL_RESULTS"),
        con=dbutil.connection(g.cfg.setting.database_file),
        params={
            "rule_version": rule_version if rule_version else g.cfg.mahjong.rule_version,
            "player_name": name,
        },
    )

    return ret_data


def read_memberslist():
    """メンバー情報/チーム情報の読み込み"""

    g.cfg.member.guest_name = get_guest()
    g.cfg.member.info = get_member_info()
    g.cfg.team.info = get_team_info()

    logging.debug("guest_name: %s", g.cfg.member.guest_name)
    logging.debug("member_list: %s", g.cfg.member.lists)
    logging.debug("team_list: %s", g.cfg.team.lists)


def enumeration_all_members() -> list[str]:
    """メンバーとチームをすべて列挙する

    Returns:
        list[str]: _description_
    """

    member_list: list["MemberDataDict"] = get_member_info()
    team_list: list["TeamDataDict"] = get_team_info()
    ret_list: list[str] = []

    # チャンネル個別設定探索
    for section_name in g.cfg.main_parser.sections():
        if channel_config := g.cfg.main_parser[section_name].get("channel_config"):
            g.cfg.overwrite(Path(channel_config), "setting")
            member_list.extend(get_member_info())
            team_list.extend(get_team_info())

    for x in member_list:
        ret_list.append(x.get("name"))
        ret_list.extend(x.get("alias"))
    ret_list.extend([x.get("team") for x in team_list])

    return list(set(ret_list))
