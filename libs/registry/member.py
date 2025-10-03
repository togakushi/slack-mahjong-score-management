"""
libs/registry/member.py
"""

import logging

import libs.global_value as g
from libs.data import lookup, modify
from libs.utils import dbutil, textutil, validator


def append(argument: list) -> dict:
    """メンバー追加

    Args:
        argument (list): 登録情報
            - argument[0]: 登録するメンバー名
            - argument[1]: 登録する別名

    Returns:
        dict: 処理結果
    """

    resultdb = dbutil.connection(g.cfg.setting.database_file)

    ret: bool = False
    dbupdate_flg: bool = False
    msg: str = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        new_name = textutil.str_conv(argument[0], "h2z")
        rows = resultdb.execute("select count() from member")
        count = rows.fetchone()[0]
        if count > g.cfg.member.registration_limit:
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = validator.check_namepattern(new_name, "member")
            if ret:
                resultdb.execute(
                    "insert into member(name) values (?)",
                    (new_name,)
                )
                resultdb.execute(
                    "insert into alias(name, member) values (?,?)",
                    (new_name, new_name)
                )
                msg = f"「{new_name}」を登録しました。"
                logging.notice(f"add new member: {new_name}")  # type: ignore

    if len(argument) == 2:  # 別名登録
        new_name = textutil.str_conv(argument[0], "h2z")
        nic_name = textutil.str_conv(argument[1], "h2z")
        registration_flg = True
        rows = resultdb.execute("select count() from alias where member=?", (new_name,))
        count = rows.fetchone()[0]
        if count == 0:
            msg = f"「{new_name}」はまだ登録されていません。"
            registration_flg = False
        if count > g.cfg.member.alias_limit:
            msg = "登録上限を超えています。"
            registration_flg = False

        if registration_flg:  # 登録処理
            ret, msg = validator.check_namepattern(nic_name, "member")
            if ret:
                resultdb.execute("insert into alias(name, member) values (?,?)", (nic_name, new_name))
                msg = f"「{new_name}」に「{nic_name}」を追加しました。"
                logging.notice(f"add alias: {new_name} -> {nic_name}")  # type: ignore
                dbupdate_flg = True

        if dbupdate_flg:
            rows = resultdb.execute(
                """
                select distinct name from (
                    select p1_name as name from result
                    union all select p2_name from result
                    union all select p3_name from result
                    union all select p4_name from result
                    union all select name from remarks
                );
                """
            )
            name_list = [row["name"] for row in rows.fetchall()]

            if {nic_name, textutil.str_conv(nic_name, "k2h"), textutil.str_conv(nic_name, "h2k")} & set(name_list):
                msg += modify.db_backup()
                for tbl, col in [("result", f"p{x}_name") for x in range(1, 5)] + [("remarks", "name")]:
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, nic_name))
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, textutil.str_conv(nic_name, "k2h")))
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, textutil.str_conv(nic_name, "h2k")))
                msg += "\nデータベースを更新しました。"

    resultdb.commit()
    resultdb.close()

    g.member_list = lookup.db.get_member_list()
    return {"メンバー追加": msg}


def remove(argument: list) -> dict:
    """メンバー削除

    Args:
        argument (list): 削除情報
            - argument[0]: 削除するメンバー名
            - argument[1]: 削除する別名

    Returns:
        dict: slackにpostする内容(処理結果)
    """

    resultdb = dbutil.connection(g.cfg.setting.database_file)
    msg = "使い方が間違っています。"

    if len(argument) == 1:  # メンバー削除
        new_name = textutil.str_conv(argument[0], "h2z")
        if new_name in g.member_list:
            resultdb.execute("delete from member where name=?", (new_name,))
            resultdb.execute("delete from alias where member=?", (new_name,))
            msg = f"「{new_name}」を削除しました。"
            logging.notice(f"remove member: {new_name}")  # type: ignore
        else:
            msg = f"「{new_name}」は登録されていません。"

    if len(argument) == 2:  # 別名削除
        new_name = textutil.str_conv(argument[0], "h2z")
        nic_name = textutil.str_conv(argument[1], "h2z")
        if nic_name in g.member_list:
            resultdb.execute(
                "delete from alias where name=? and member=?",
                (nic_name, new_name)
            )
            msg = f"「{new_name}」から「{nic_name}」を削除しました。"
            logging.notice(f"alias remove: {new_name} -> {nic_name}")  # type: ignore
        else:
            msg = f"「{new_name}」に「{nic_name}」は登録されていません。"

    resultdb.commit()
    resultdb.close()

    g.member_list = lookup.db.get_member_list()
    return {"メンバー削除": msg}
