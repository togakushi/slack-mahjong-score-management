"""
lib/data/lookup/internal.py
"""

import lib.global_value as g


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


def get_teammates():
    """所属チームのチームメイトを返す

    Returns:
        list: メンバーリスト
    """

    member_list: list = []
    team_data = [x for x in g.team_list if x["team"] == g.params["player_name"]]
    if team_data:
        if team_data[0]["member"]:
            member_list = team_data[0]["member"].split(",")
        else:
            member_list = ["未エントリー"]

    return (member_list)


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
            if name in x["member"].split(","):
                team = x["team"]

    return (team)
