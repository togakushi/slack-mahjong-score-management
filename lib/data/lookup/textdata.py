"""
lib/data/lookup/textdata.py
"""

import sqlite3

import lib.global_value as g
from lib.utils import textutil


# slack出力用
def get_members_list():
    """登録済みのメンバー一覧を取得する(slack出力用)

    Returns:
        Tuple[str, str]:
            - str: post時のタイトル
            - str: メンバー一覧
    """

    title = "登録済みメンバー一覧"
    padding = textutil.count_padding(list(set(g.member_list.values())))
    msg = "# 表示名{}：登録されている名前 #\n".format(" " * (padding - 8))  # pylint: disable=consider-using-f-string

    for pname in set(g.member_list.values()):
        name_list = []
        for alias, name in g.member_list.items():
            if name == pname:
                name_list.append(alias)
        msg += "{}{}：{}\n".format(  # pylint: disable=consider-using-f-string
            pname,
            " " * (padding - textutil.len_count(pname)),
            ", ".join(name_list),
        )

    return (title, msg)


def get_team_list():
    """チームの登録状況を表示する(slack出力用)

    Returns:
        str: slackにpostする内容
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row
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

    return (msg)
