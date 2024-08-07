import re
import sqlite3
from itertools import chain

import lib.function as f
import lib.database as d
from lib.function import global_value as g
from lib.command.member import NameReplace


def check_namepattern(name):
    """
    登録制限チェック

    Parameters
    ----------
    name : str
        チェック対象文字列

    Returns
    -------
    bool : True / False
        制限チェック結果

    msg : text
        制限理由
    """

    # 登録済みチームかチェック
    if name in [i for i in g.team_list.values()]:
        return(False, f"チーム名「{name}」はすでに使用されています。")
    if f.common.KANA2HIRA(name) in [f.common.KANA2HIRA(i) for i in g.team_list.values()]: # ひらがな
        return(False, f"チーム名「{name}」はすでに使用されています。")
    if f.common.HIRA2KANA(name) in [f.common.HIRA2KANA(i) for i in g.team_list.values()]: # カタカナ
        return(False, f"チーム名「{name}」はすでに使用されています。")

    # 登録規定チェック
    if len(name) > g.config["team"].getint("character_limit", 8): # 文字制限
        return(False, "登録可能文字数を超えています。")
    if name == g.guest_name: # 登録NGプレイヤー名
        return(False, "使用できない名称です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable(): # 禁則記号
        return(False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    chk_target_days, _, _, chk_command_option = f.common.argument_analysis([name])
    if chk_target_days:
        return(False, "検索範囲指定に使用される単語は登録できません。")
    if chk_command_option:
        return(False, "オプションに使用される単語は登録できません。")

    commandlist = [i for i in g.commandword.values()]
    commandlist.extend([g.config["setting"].get("slash_commandname")])
    commandlist.extend([g.config["setting"].get("remarks_word")])
    commandlist.extend([g.config["search"].get("keyword")])
    commandlist.extend([x for x, _ in g.config.items("alias")])
    commandlist.extend(chain.from_iterable([y.split(",") for _, y in g.config.items("alias")]))
    if name in set(commandlist):
        return(False, "コマンドに使用される単語は登録できません。")

    return(True, "OK")


def create(argument):
    """
    チーム作成

    Parameters
    ----------
    argument : list
        argument[0] = 作成するチーム名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    ret = False
    msg = "使い方が間違っています。"

    if len(argument) == 1: # 新規追加
        team_name = f.common.HAN2ZEN(argument[0])
        g.logging.notice(f"New Team: {team_name}") # type: ignore

        if len(g.team_list) > g.config["team"].getint("registration_limit", 255):
            msg = f"登録上限を超えています。"
        else: # 登録処理
            ret, msg = check_namepattern(team_name)
            if ret:
                resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
                resultdb.row_factory = sqlite3.Row
                resultdb.execute(f"insert into team(name) values (?)", (team_name,))
                resultdb.commit()
                resultdb.close()
                f.configure.read_memberslist()
                msg = f"チーム「{team_name}」を登録しました。"

    return(msg)


def delete(argument):
    """
    チーム削除

    Parameters
    ----------
    argument : list
        argument[0] = 削除するチーム名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1: # 新規追加
        team_name = f.common.HAN2ZEN(argument[0])
        g.logging.notice(f"Team delete: {team_name}") # type: ignore

        if not team_name in g.team_list.values(): # 未登録チームチェック
            msg = f"チーム「{team_name}」は登録されていません。"
        else:
            msg = d.common.database_backup()
            team_id = [k for k, v in g.team_list.items() if v == team_name][0]
            resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
            resultdb.execute(f"delete from team where id = ?", (team_id,))
            resultdb.execute(f"update member set team_id = null where team_id = ?", (team_id,))
            resultdb.commit()
            resultdb.close()
            f.configure.read_memberslist()
            msg += f"\nチーム「{team_name}」を削除しました。"

    return(msg)


def append(argument):
    """
    チーム所属

    Parameters
    ----------
    argument : list
        argument[0] = 所属させるチーム名
        argument[1] = 所属するプレイヤー名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1: # 新規作成
        msg = create(argument)

    if len(argument) == 2: # チーム所属
        g.opt.unregistered_replace = False

        team_name = f.common.HAN2ZEN(argument[0])
        player_name = NameReplace(argument[1])
        g.logging.notice(f"Team participation: {team_name} -> {player_name}") # type: ignore

        registration_flg = True
        team_id = None

        if not team_name in g.team_list.values(): # 未登録チームチェック
            msg = f"チーム「{team_name}」はまだ登録されていません。"
            registration_flg = False
        else:
            team_id = [k for k, v in g.team_list.items() if v == team_name][0]

        if not player_name in g.member_list.keys(): # 未登録プレイヤーチェック 
            msg = f"「{player_name}」はレギュラーメンバーではありません。"
            registration_flg = False

        # 登録上限を超えていないか？
        #select count() from member where team_id=? group by team_id;
        #rows = resultdb.execute("select count() from team where name=?", (team_name,))
        #count = rows.fetchone()[0]
        #if count > g.config["team"].getint("member_limit", 16):
        #    msg = f"登録上限を超えています。"
        #    registration_flg = False

        if registration_flg and team_id: # 登録処理
            resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
            resultdb.execute("update member set team_id = ? where name = ?", (team_id, player_name))
            resultdb.commit()
            resultdb.close()
            f.configure.read_memberslist()
            msg = f"チーム「{team_name}」に「{player_name}」を所属させました。"

    return(msg)


def remove(argument):
    """
    チームから除名

    Parameters
    ----------
    argument : list
        argument[0] = 対象チーム名
        argument[1] = チームから離脱するプレイヤー名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    msg = "使い方が間違っています。"

    if len(argument) == 2: # 別名削除
        g.opt.unregistered_replace = False

        team_name = f.common.HAN2ZEN(argument[0])
        player_name = NameReplace(argument[1])
        g.logging.notice(f"Team breakaway: {team_name} -> {player_name}") # type: ignore

        registration_flg = True
        team_id = None

        if not team_name in g.team_list.values(): # 未登録チームチェック
            msg = f"チーム「{team_name}」は登録されていません。"
            registration_flg = False
        else:
            team_id = [k for k, v in g.team_list.items() if v == team_name][0]

        if not player_name in g.member_list.keys(): # 未登録プレイヤーチェック 
            msg = f"「{player_name}」はレギュラーメンバーではありません。"
            registration_flg = False

        if registration_flg and team_id: # 登録処理
            resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
            resultdb.execute("update member set team_id = null where name = ?", (player_name,))
            resultdb.commit()
            resultdb.close()
            f.configure.read_memberslist()
            msg = f"チーム「{team_name}」から「{player_name}」を離脱させました。"

    return(msg)


def list():
    """
    チームの登録状況を表示する
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
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

    return(msg)


def clear():
    """
    全チーム削除

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    msg = d.common.database_backup()

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    resultdb.execute("drop table team")
    resultdb.execute("update member set team_id = null")
    resultdb.commit()
    resultdb.close()

    d.initialization.initialization_resultdb()
    f.configure.read_memberslist()

    return(msg)
