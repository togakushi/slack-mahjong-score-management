"""
libs/data/lookup.py
"""

import logging
from configparser import ConfigParser
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

import pandas as pd

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.utils import dbutil

if TYPE_CHECKING:
    from pathlib import Path

    from libs.types import MemberDataDict, PlaceholderDict, TeamDataDict


def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type,
    fallback: Union[bool, int, float, str, list, None] = None,
) -> Any:
    """設定値取得

    Args:
        config_file (Path): 設定ファイルパス
        section (str): セクション名
        name (str): 項目名
        val_type (type): 取り込む値の型 (bool, int, float, str, list)
        fallback (Union[bool, int, float, str, list], optional): 項目が見つからない場合に返す値. Defaults to None

    Returns:
        Any: 取得した値
            - 実際に返す型: Union[int, float, bool, str, list, None]
    """

    value: Union[int, float, bool, str, list, None] = fallback
    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")

    if parser.has_option(section, name):
        match val_type:
            case x if x is int:
                value = parser.getint(section, name)
            case x if x is float:
                value = parser.getfloat(section, name)
            case x if x is bool:
                value = parser.getboolean(section, name)
            case x if x is str:
                value = parser.get(section, name)
            case x if x is list:
                value = [x.strip() for x in parser.get(section, name).split(",")]
            case _:
                value = parser.get(section, name)

    return value


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
        params["starttime"] = cast(ExtDt, params["starttime"]).format("sql")
        params["endtime"] = cast(ExtDt, params["endtime"]).format("sql")
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

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        rows = conn.execute("select name, id from member where id != 0;")
        id_list = dict(rows.fetchall())

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        rows = conn.execute("select name, member from alias")
        alias_list = dict(rows.fetchall())

    for name, id in id_list.items():
        ret.append(
            {
                "id": id,
                "name": name,
                "alias": [k for k, v in alias_list.items() if v == name],
            }
        )

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
            ret.append(
                {
                    "id": int(row["id"]),
                    "team": str(row["team"]),
                    "member": str(row["member"]).split(","),
                }
            )

    return ret


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
    rule_dict = {f"rule_{idx}": name for idx, name in enumerate(set(rule_list))}

    try:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
            table_count = conn.execute(
                "select count() from sqlite_master where type='view' and name='game_results';",
            ).fetchall()[0][0]

            if table_count:
                sql = "select min(playtime) from game_results where rule_version in (<<rule_list>>);".replace("<<rule_list>>", ":" + ", :".join(rule_dict))
                record = conn.execute(sql, rule_dict).fetchall()[0][0]
                if record:
                    ret = ExtDt(str(record)) - {"hour": 0, "minute": 0, "second": 0, "microsecond": 0, "hours": g.cfg.setting.time_adjust}
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
        list[str]: メンバー名(別名含む)/チーム名のリスト
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

    for member in member_list:
        ret_list.append(member.get("name"))
        ret_list.extend(member.get("alias"))
    ret_list.extend([team.get("team") for team in team_list])

    return list(set(ret_list))
