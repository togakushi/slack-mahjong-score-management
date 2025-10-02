"""
libs/registry/team.py
"""

import logging

import libs.global_value as g
from libs.data import initialization, modify
from libs import configuration
from libs.utils import dbutil, formatter, textutil, validator


def create(argument: list) -> dict[str, str]:
    """チーム作成

    Args:
        argument (list): 作成するチーム名

    Returns:
        dict[str, str]: 処理結果
    """

    ret = False
    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        team_name = textutil.str_conv(argument[0], "h2z")
        if len(g.team_list) > g.cfg.team.registration_limit:
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = validator.check_namepattern(team_name, "team")
            if ret:
                resultdb = dbutil.connection(g.cfg.setting.database_file)
                resultdb.execute(
                    "insert into team(name) values (?)",
                    (team_name,)
                )
                resultdb.commit()
                resultdb.close()
                configuration.read_memberslist()
                msg = f"チーム「{team_name}」を登録しました。"
                logging.notice("add new team: %s", team_name)  # type: ignore

    return {"チーム作成": msg}


def delete(argument: list) -> dict[str, str]:
    """チーム削除

    Args:
        argument (list): 削除するチーム名

    Returns:
        dict[str, str]: 処理結果
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        team_name = textutil.str_conv(argument[0], "h2z")
        if team_name not in [x["team"] for x in g.team_list]:  # 未登録チームチェック
            msg = f"チーム「{team_name}」は登録されていません。"
        else:
            msg = modify.db_backup()
            team_id = [x["id"] for x in g.team_list if x["team"] == team_name][0]
            resultdb = dbutil.connection(g.cfg.setting.database_file)
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
            configuration.read_memberslist()
            msg += f"\nチーム「{team_name}」を削除しました。"
            logging.notice("team delete: %s", team_name)  # type: ignore

    return {"チーム削除": msg}


def append(argument: list) -> dict[str, str]:
    """チーム所属

    Args:
        argument (list): 登録情報
            - argument[0]: 所属させるチーム名
            - argument[1]: 所属するメンバー名

    Returns:
        dict[str, str]: 処理結果
    """

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規作成
        (msg,) = create(argument).values()

    if len(argument) == 2:  # チーム所属
        g.params.update(unregistered_replace=False)

        team_name = textutil.str_conv(argument[0], "h2z")
        player_name = formatter.name_replace(argument[1])
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
        # if count > g.cfg.team.member_limit:
        #    msg = f"登録上限を超えています。"
        #    registration_flg = False

        if registration_flg and team_id:  # 登録処理
            resultdb = dbutil.connection(g.cfg.setting.database_file)
            resultdb.execute(
                "update member set team_id = ? where name = ?",
                (team_id, player_name)
            )
            resultdb.commit()
            resultdb.close()
            configuration.read_memberslist()
            msg = f"チーム「{team_name}」に「{player_name}」を所属させました。"
            logging.notice("team participation: %s -> %s", team_name, player_name)  # type: ignore

    return {"チーム所属": msg}


def remove(argument: list) -> dict[str, str]:
    """チームから除名

    Args:
        argument (list): 登録情報
            - argument[0]: 対象チーム名
            - argument[1]: チームから離脱するメンバー名

    Returns:
        dict[str, str]: 処理結果
    """

    msg = "使い方が間違っています。"

    resultdb = dbutil.connection(g.cfg.setting.database_file)

    if len(argument) == 1:
        (msg,) = delete(argument).values()

    if len(argument) == 2:  # チーム名指
        g.params.update(unregistered_replace=False)
        team_name = textutil.str_conv(argument[0], "h2z")
        player_name = formatter.name_replace(argument[1])

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
            resultdb = dbutil.connection(g.cfg.setting.database_file)
            resultdb.execute(
                "update member set team_id = null where name = ?",
                (player_name,)
            )
            resultdb.commit()
            resultdb.close()
            configuration.read_memberslist()
            msg = f"チーム「{team_name}」から「{player_name}」を離脱させました。"
            logging.notice("team breakaway: %s -> %s", team_name, player_name)  # type: ignore

    return {"チーム除名": msg}


def clear() -> dict[str, str]:
    """全チーム削除

    Returns:
        dict[str, str]: slackにpostする内容
    """

    msg = modify.db_backup()

    resultdb = dbutil.connection(g.cfg.setting.database_file)
    resultdb.execute("update member set team_id = null;")
    resultdb.execute("drop table team;")
    resultdb.execute("delete from sqlite_sequence where name = 'team';")
    resultdb.commit()
    resultdb.close()

    initialization.initialization_resultdb()
    configuration.read_memberslist()

    return {"全チーム削除": msg}
