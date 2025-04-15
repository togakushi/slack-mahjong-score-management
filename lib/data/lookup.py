"""
lib/data/lookup.py
"""

import sqlite3
from contextlib import closing
from datetime import datetime

import lib.global_value as g
from lib.data import loader
from lib.utils import textutil


def get_member_id(name: str | None = None) -> dict:
    """メンバーのIDを返す

    Args:
        name (str | None, optional): 指定メンバーのみ. Defaults to None.

    Returns:
        dict: メンバー名とIDのペア
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file)
    rows = resultdb.execute("select name, id from member;")
    id_list = dict(rows.fetchall())
    resultdb.close()

    if name in id_list:
        return ({name: id_list[name]})
    return (id_list)


def member_info(name):
    """指定メンバーの記録情報を返す

    Args:
        name (str): 対象メンバー

    Returns:
        dict: 記録情報
    """

    sql = """
        select
            count() as game_count,
            min(ts) as first_game,
            max(ts) as last_game,
            max(rpoint) as max_rpoint,
            min(rpoint) as min_rpoint
        from
            --[individual] individual_results as results
            --[team] team_results as results
        where
            rule_version = ?
            and name = ?
    """

    sql = loader.query_modification(sql)
    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(sql, (g.cfg.mahjong.rule_version, name))
    ret = dict(rows.fetchone())
    resultdb.close()
    return (ret)


def which_team(name):
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


def rule_version() -> dict:
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule: dict = {}
    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        ret = cur.execute(
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

    return (rule)


def word_list(word_type: int = 0) -> list:
    """登録済みワードリストを取得する

    Args:
        word_type (int, optional): 取得するタイプ. Defaults to 0.

    Returns:
        list: 取得結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
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

    return (ret)


def exsist_record(ts: str) -> dict:
    """記録されているゲーム結果を返す

    Args:
        ts (str): 検索するタイムスタンプ

    Returns:
        dict: 検索結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        row = cur.execute("select * from result where ts=?", (ts,)).fetchone()

    if row:
        return (dict(row))
    return ({})


def first_record() -> datetime:
    """最初のゲーム記録時間を返す

    Returns:
        datetime: 最初のゲーム記録時間
    """

    ret = datetime.now()
    with closing(sqlite3.connect(g.cfg.db.database_file)) as resultdb:
        table_count = resultdb.execute(
            "select count() from sqlite_master where type='view' and name='game_results'",
        ).fetchall()[0][0]

        if table_count:
            record = resultdb.execute(
                "select min(playtime) from game_results"
            ).fetchall()[0][0]
            if record:
                ret = datetime.fromisoformat(record)

    return (ret)


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
