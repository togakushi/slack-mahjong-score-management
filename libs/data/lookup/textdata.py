"""
libs/data/lookup/textdata.py
"""

from table2ascii import Alignment, PresetStyle, table2ascii

import libs.global_value as g
from libs.utils import dbutil


def get_members_list() -> str:
    """登録済みのメンバー一覧を取得する

    Returns:
        str: メンバーリスト
    """

    name_list: list = []
    for pname in set(g.cfg.member.list.values()):
        name_list.append(
            [
                pname,
                ", ".join([k for k, v in g.cfg.member.list.items() if v == pname]),
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

    resultdb = dbutil.connection(g.cfg.setting.database_file)
    cur = resultdb.execute("""
        select
            team.name,
            ifnull(
                group_concat(member.name),
                "未エントリー"
            )
        from
            team
        left join member on
            team.id = member.team_id
        group by
            team.name
    """)
    team_data = dict(cur.fetchall())

    if len(team_data) == 0:
        msg = "チームは登録されていません。"
    else:
        msg = ""
        for k, v in team_data.items():
            msg += f"{k}\n"
            for p in v.split(","):
                msg += f"\t{p}\n"
            msg += "\n"

    return msg
