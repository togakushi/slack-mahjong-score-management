import logging
import sqlite3

import lib.global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


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

    member = []
    team_data = [x for x in g.team_list if x["team"] == g.prm.player_name]
    if team_data:
        if team_data[0]["member"]:
            member = team_data[0]['member'].split(",")
        else:
            member = ["未エントリー"]

    return (member)


def create(argument):
    """チーム作成

    Args:
        argument (list): 作成するチーム名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    ret = False
    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        team_name = f.common.han_to_zen(argument[0])
        if len(g.team_list) > g.cfg.config["team"].getint("registration_limit", 255):
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = f.common.check_namepattern(team_name, "team")
            if ret:
                resultdb = sqlite3.connect(
                    g.cfg.db.database_file,
                    detect_types=sqlite3.PARSE_DECLTYPES,
                )
                resultdb.row_factory = sqlite3.Row
                resultdb.execute(
                    "insert into team(name) values (?)",
                    (team_name,)
                )
                resultdb.commit()
                resultdb.close()
                c.member.read_memberslist()
                msg = f"チーム「{team_name}」を登録しました。"
                logging.notice("add new team: %s", team_name)  # type: ignore

    return (msg)


def delete(argument):
    """チーム削除

    Args:
        argument (list): 削除するチーム名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        team_name = f.common.han_to_zen(argument[0])
        if team_name not in [x["team"] for x in g.team_list]:  # 未登録チームチェック
            msg = f"チーム「{team_name}」は登録されていません。"
        else:
            msg = d.common.db_backup()
            team_id = [x["id"] for x in g.team_list if x["team"] == team_name][0]
            resultdb = sqlite3.connect(
                g.cfg.db.database_file,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            resultdb.execute(
                "delete from team where id = ?",
                (team_id,)
            )
            resultdb.execute(
                "update member set team_id = null where team_id = ?",
                (team_id,)
            )
            resultdb.commit()
            resultdb.close()
            c.member.read_memberslist()
            msg += f"\nチーム「{team_name}」を削除しました。"
            logging.notice("team delete: %s", team_name)  # type: ignore

    return (msg)


def append(argument):
    """チーム所属

    Args:
        argument (list): 登録情報
            - argument[0]: 所属させるチーム名
            - argument[1]: 所属するメンバー名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規作成
        msg = create(argument)

    if len(argument) == 2:  # チーム所属
        g.opt.unregistered_replace = False

        team_name = f.common.han_to_zen(argument[0])
        player_name = c.member.name_replace(argument[1])
        registration_flg = True
        team_id = None

        if team_name not in [x["team"] for x in g.team_list]:  # 未登録チームチェック
            msg = f"チーム「{team_name}」はまだ登録されていません。"
            registration_flg = False
        else:
            team_id = [x["id"] for x in g.team_list if x["team"] == team_name][0]

        if player_name not in g.member_list:  # 未登録プレイヤーチェック
            msg = f"「{player_name}」はレギュラーメンバーではありません。"
            registration_flg = False

        # 登録上限を超えていないか？
        # select count() from member where team_id=? group by team_id;
        # rows = resultdb.execute("select count() from team where name=?", (team_name,))
        # count = rows.fetchone()[0]
        # if count > g.cfg.config["team"].getint("member_limit", 16):
        #    msg = f"登録上限を超えています。"
        #    registration_flg = False

        if registration_flg and team_id:  # 登録処理
            resultdb = sqlite3.connect(
                g.cfg.db.database_file,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            resultdb.execute(
                "update member set team_id = ? where name = ?",
                (team_id, player_name)
            )
            resultdb.commit()
            resultdb.close()
            c.member.read_memberslist()
            msg = f"チーム「{team_name}」に「{player_name}」を所属させました。"
            logging.notice("team participation: %s -> %s", team_name, player_name)  # type: ignore

    return (msg)


def remove(argument):
    """チームから除名

    Args:
        argument (_type_): 登録情報
            - argument[0]: 対象チーム名
            - argument[1]: チームから離脱するメンバー名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row

    msg = "使い方が間違っています。"

    # todo: argument == 1のときの処理

    if len(argument) == 2:  # チーム名指
        g.opt.unregistered_replace = False
        team_name = f.common.han_to_zen(argument[0])
        player_name = c.member.name_replace(argument[1])

        registration_flg = True
        team_id = None

        if team_name not in [x["team"] for x in g.team_list]:  # 未登録チームチェック
            msg = f"チーム「{team_name}」は登録されていません。"
            registration_flg = False
        else:
            team_id = [x["id"] for x in g.team_list if x["team"] == team_name][0]

        if player_name not in g.member_list:  # 未登録プレイヤーチェック
            msg = f"「{player_name}」はレギュラーメンバーではありません。"
            registration_flg = False

        if registration_flg and team_id:  # 登録処理
            resultdb = sqlite3.connect(
                g.cfg.db.database_file,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            resultdb.execute(
                "update member set team_id = null where name = ?",
                (player_name,)
            )
            resultdb.commit()
            resultdb.close()
            c.member.read_memberslist()
            msg = f"チーム「{team_name}」から「{player_name}」を離脱させました。"
            logging.notice("team breakaway: %s -> %s", team_name, player_name)  # type: ignore

    return (msg)


def get_list():
    """チームの登録状況を表示する

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


def clear():
    """全チーム削除

    Returns:
        str: slackにpostする内容
    """

    msg = d.common.db_backup()

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row

    resultdb.execute("update member set team_id = null;")
    resultdb.execute("drop table team;")
    resultdb.execute("delete from sqlite_sequence where name = 'team';")
    resultdb.commit()
    resultdb.close()

    d.initialization.initialization_resultdb()
    c.member.read_memberslist()

    return (msg)
