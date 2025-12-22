"""
libs/data/lookup/textdata.py
"""

from table2ascii import Alignment, PresetStyle, table2ascii

import libs.global_value as g


def get_members_list() -> str:
    """登録済みのメンバー一覧を取得する

    Returns:
        str: メンバーリスト
    """

    name_list: list = []
    for pname in g.cfg.member.list:
        name_list.append(
            [
                pname,
                ", ".join([k for k, v in g.cfg.member.info.items() if v == pname]),
            ],
        )

    if name_list:
        output = table2ascii(
            header=["表示名", "登録されている名前"],
            body=name_list,
            alignments=[Alignment.LEFT, Alignment.LEFT],
            style=PresetStyle.ascii_borderless,
        )
    else:
        output = "メンバーは登録されていません。"

    return output


def get_team_list() -> str:
    """チームの登録状況を取得する

    Returns:
        str: チームリスト
    """

    team_list: list = []
    for team_name in g.cfg.team.list:
        if member := ", ".join(g.cfg.team.member(team_name)):
            team_list.append([team_name, member])
        else:
            team_list.append([team_name, "未エントリー"])

    if team_list:
        output = table2ascii(
            header=["チーム名", "所属メンバー"],
            body=team_list,
            alignments=[Alignment.LEFT, Alignment.LEFT],
            style=PresetStyle.ascii_borderless,
        )
    else:
        output = "チームは登録されていません。"

    return output
