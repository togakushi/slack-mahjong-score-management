"""
libs/data/lookup/textdata.py
"""

import libs.global_value as g
from libs.utils import dbutil, textutil


def get_members_list() -> str:
    """登録済みのメンバー一覧を取得する

    Returns:
        str: メンバーリスト
    """

    padding = textutil.count_padding(list(set(g.cfg.member.list.values())))
    msg = f"# 表示名{' ' * (padding - 8)}：登録されている名前 #\n"

    for pname in set(g.cfg.member.list.values()):
        name_list = []
        for alias, name in g.cfg.member.list.items():
            if name == pname:
                name_list.append(alias)
        msg += "{}{}：{}\n".format(
            pname,
            " " * (padding - textutil.len_count(pname)),
            ", ".join(name_list),
        )

    return msg


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
