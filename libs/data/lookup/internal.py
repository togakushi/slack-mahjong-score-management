"""
libs/data/lookup/internal.py
"""

from typing import TYPE_CHECKING, Union, cast

import libs.global_value as g

if TYPE_CHECKING:
    from configparser import ConfigParser


def get_member() -> list:
    """メンバーリストを返す

    Returns:
        list: メンバーリスト
    """

    return sorted(list(set(g.member_list.values())))


def get_team() -> list:
    """チームリストを返す

    Returns:
        list: チームリスト
    """

    return ([x.get("team") for x in g.team_list])


def get_teammates(team: str) -> list:
    """指定チームのチームメイト一覧を返す

    Args:
        name (str): チェック対象のチーム名

    Returns:
        list: メンバーリスト
    """

    member_list: list = []
    if (team_data := [x for x in g.team_list if x["team"] == team]):
        if not (member_list := team_data[0]["member"]):
            member_list = ["未エントリー"]

    return member_list


def which_team(name: str) -> str | None:
    """指定メンバーの所属チームを返す

    Args:
        name (str): チェック対象のメンバー名

    Returns:
        Union[str, None]:
        - str: 所属しているチーム名
        - None: 未所属
    """

    team = None

    for x in g.team_list:
        if x["member"]:
            if name in x["member"]:
                team = x["team"]

    return team


def get_config_value(
    section: str,
    name: str,
    val_type: Union[int, float, bool, str, list, None] = None,
) -> Union[int, float, bool, str, list, None]:
    """設定値取得

    Args:
        section (str): セクション名
        name (str): 項目名
        val_type (Union[int, float, bool, str, list], optional): 型. Defaults to None

    Returns:
        Union[int, float, bool, str, list, None]: 取得した値
    """

    value: Union[int, float, bool, str, list, None] = None
    parser = cast("ConfigParser", getattr(g.cfg, "_parser"))

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
