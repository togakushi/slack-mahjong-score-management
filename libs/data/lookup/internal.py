"""
lib/data/lookup/internal.py
"""

import libs.global_value as g


def get_member() -> list:
    """メンバーリストを返す

    Returns:
        list: メンバーリスト
    """

    return (list(set(g.member_list.values())))


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
