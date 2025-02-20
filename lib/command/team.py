import logging
import re
import sqlite3

import lib.global_value as g
from cls.parameter import CommandOption
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


def check_namepattern(name):
    """登録制限チェック

    Args:
        name (str): チェックするチーム名

    Returns:
        Tuple[bool, str]:
            - bool: 制限チェック結果真偽
            - str: 制限理由
    """

    # 登録済みチームかチェック
    for x in [x["team"] for x in g.team_list]:
        if name == x:
            return (False, f"チーム名「{name}」はすでに使用されています。")
        if f.common.kata_to_hira(name) == f.common.kata_to_hira(x):  # ひらがな
            return (False, f"チーム名「{name}」はすでに使用されています。")
        if f.common.hira_to_kana(name) == f.common.hira_to_kana(x):  # カタカナ
            return (False, f"チーム名「{name}」はすでに使用されています。")

    # 登録規定チェック
    if len(name) > g.cfg.config["team"].getint("character_limit", 8):  # 文字制限
        return (False, "登録可能文字数を超えています。")
    if name == g.prm.guest_name:  # 登録NGプレイヤー名
        return (False, "使用できない名称です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        return (False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    if g.search_word.find(name):
        return (False, "検索範囲指定に使用される単語は登録できません。")

    chk = CommandOption()
    chk.check([name])
    if vars(chk):
        return (False, "オプションに使用される単語は登録できません。")

    if name in g.cfg.word_list():
        return (False, "コマンドに使用される単語は登録できません。")

    return (True, "OK")


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
        logging.notice("New Team: %s", team_name)

        if len(g.team_list) > g.cfg.config["team"].getint("registration_limit", 255):
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = check_namepattern(team_name)
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
        logging.notice("Team delete: %s", team_name)

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
        logging.notice("Team participation: %s -> %s", team_name, player_name)

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
        logging.notice("Team breakaway: %s -> %s", team_name, player_name)

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
