"""
lib/command/member.py
"""

import logging
import re
import sqlite3
import random

import lib.global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def read_memberslist(log=True):
    """メンバー/チームリスト読み込み

    Args:
        log (bool, optional): 読み込み時に内容をログに出力する. Defaults to True.
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    rows = resultdb.execute("select name from member where id=0")
    g.cfg.member.guest_name = rows.fetchone()[0]

    rows = resultdb.execute("select name, member from alias")
    g.member_list = dict(rows.fetchall())

    rows = resultdb.execute(
        """
            select
                team.id as id,
                team.name as team,
                group_concat(member.name) as member
            from
                team
            left join member on
                team.id == member.team_id
            group by
                team.id
        """)

    g.team_list = []
    for row in rows.fetchall():
        g.team_list.append(
            dict(zip(["id", "team", "member"], row))
        )

    resultdb.close()

    if log:
        logging.notice(f"guest_name: {g.cfg.member.guest_name}")  # type: ignore
        logging.notice(f"member_list: {set(g.member_list.values())}")  # type: ignore
        logging.notice(f"team_list: {[x['team'] for x in g.team_list]}")  # type: ignore


def name_replace(pname: str, add_mark: bool = False) -> str:
    """表記ブレ修正(正規化)

    Args:
        pname (str): 対象プレイヤー名
        add_mark (bool, optional): ゲストマークを付与する. Defaults to False.

    Returns:
        str: 表記ブレ修正後のプレイヤー名
    """

    pname = f.common.han_to_zen(pname)
    check_list = list(set(g.member_list.keys()))

    if pname in check_list:
        return (g.member_list[pname])

    # 敬称削除
    honor = r"(くん|さん|ちゃん|クン|サン|チャン|君)$"
    if re.match(fr".*{honor}", pname):
        if not re.match(fr".*(っ|ッ|ー){honor}", pname):
            pname = re.sub(fr"{honor}", "", pname)
    if pname in check_list:
        return (g.member_list[pname])

    # ひらがな、カタカナでチェック
    if f.common.kata_to_hira(pname) in check_list:
        return (g.member_list[f.common.kata_to_hira(pname)])
    if f.common.hira_to_kana(pname) in check_list:
        return (g.member_list[f.common.hira_to_kana(pname)])

    # メンバーリストに見つからない場合
    if g.params.get("unregistered_replace"):
        return (g.cfg.member.guest_name)
    if add_mark:
        return (f"{pname}({g.cfg.setting.guest_mark})")

    return (pname)


def anonymous_mapping(name_list: list, initial: int = 0) -> dict:
    """名前リストから変換用辞書を生成

    Args:
        name_list (list): 名前リスト
        initial (int, optional): インデックス初期値. Defaults to 0.

    Returns:
        dict: マッピング用辞書
    """

    ret: dict = {}

    if g.params.get("individual", True):
        prefix = "Player"
        id_list = c.member.get_member_id()
    else:
        prefix = "Team"
        id_list = {x["team"]: x["id"] for x in g.team_list}

    if len(name_list) == 1:
        name = name_list[0]
        if name in id_list:
            idx = id_list[name]
        else:
            idx = int(random.random() * 100 + 100)
        ret[name] = f"{prefix}_{idx + initial:03d}"
    else:
        random.shuffle(name_list)
        for idx, name in enumerate(name_list):
            ret[name] = f"{prefix}_{idx + initial:03d}"

    return (ret)


def count_padding(data):
    """プレイヤー名一覧の中の最も長い名前の文字数を返す

    Args:
        data (list, dict): 対象プレイヤー名の一覧

    Returns:
        int: 文字数
    """

    name_list = []

    if isinstance(data, list):
        name_list = data

    if isinstance(data, dict):
        for i in data.keys():
            for name in [data[i][x]["name"] for x in g.wind[0:4]]:
                if name not in name_list:
                    name_list.append(name)

    if name_list:
        return (max(f.common.len_count(x) for x in name_list))
    return (0)


def get_members_list():
    """登録済みのメンバー一覧を取得する(slack出力用)

    Returns:
        Tuple[str, str]:
            - str: post時のタイトル
            - str: メンバー一覧
    """

    title = "登録済みメンバー一覧"
    padding = c.member.count_padding(list(set(g.member_list.values())))
    msg = "# 表示名{}：登録されている名前 #\n".format(" " * (padding - 8))  # pylint: disable=consider-using-f-string

    for pname in set(g.member_list.values()):
        name_list = []
        for alias, name in g.member_list.items():
            if name == pname:
                name_list.append(alias)
        msg += "{}{}：{}\n".format(  # pylint: disable=consider-using-f-string
            pname,
            " " * (padding - f.common.len_count(pname)),
            ", ".join(name_list),
        )

    return (title, msg)


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

    sql = d.common.query_modification(sql)
    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(sql, (g.cfg.mahjong.rule_version, name))
    ret = dict(rows.fetchone())
    resultdb.close()
    return (ret)


def member_append(argument):
    """メンバー追加

    Args:
        argument (list): 登録情報
            - argument[0]: 登録するメンバー名
            - argument[1]: 登録する別名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = False
    dbupdate_flg = False
    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        new_name = f.common.han_to_zen(argument[0])
        rows = resultdb.execute("select count() from member")
        count = rows.fetchone()[0]
        if count > g.cfg.config["member"].getint("registration_limit", 255):
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = f.common.check_namepattern(new_name, "member")
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
        new_name = f.common.han_to_zen(argument[0])
        nic_name = f.common.han_to_zen(argument[1])
        registration_flg = True
        rows = resultdb.execute("select count() from alias where member=?", (new_name,))
        count = rows.fetchone()[0]
        if count == 0:
            msg = f"「{new_name}」はまだ登録されていません。"
            registration_flg = False
        if count > g.cfg.config["member"].getint("alias_limit", 16):
            msg = "登録上限を超えています。"
            registration_flg = False

        if registration_flg:  # 登録処理
            ret, msg = f.common.check_namepattern(nic_name, "member")
            if ret:
                resultdb.execute("insert into alias(name, member) values (?,?)", (nic_name, new_name))
                msg = f"「{new_name}」に「{nic_name}」を追加しました。"
                logging.notice(f"add alias: {new_name} -> {nic_name}")  # type: ignore
                dbupdate_flg = True

        if dbupdate_flg:
            rows = resultdb.execute(
                """
                select name from (
                    select p1_name as name from result
                    union all select p2_name from result
                    union all select p3_name from result
                    union all select p4_name from result
                    union all select name from remarks
                ) group by name;
                """
            )
            name_list = [row["name"] for row in rows.fetchall()]

            if {nic_name, f.common.kata_to_hira(nic_name), f.common.hira_to_kana(nic_name)} & set(name_list):
                msg += d.common.db_backup()
                for tbl, col in [("result", f"p{x}_name") for x in range(1, 5)] + [("remarks", "name")]:
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, nic_name))
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, f.common.kata_to_hira(nic_name)))
                    resultdb.execute(f"update {tbl} set {col}=? where {col}=?", (new_name, f.common.hira_to_kana(nic_name)))
                msg += "\nデータベースを更新しました。"

    resultdb.commit()
    resultdb.close()
    read_memberslist()

    return (msg)


def member_remove(argument):
    """メンバー削除

    Args:
        argument (list): 削除情報
            - argument[0]: 削除するメンバー名
            - argument[1]: 削除する別名

    Returns:
        str: slackにpostする内容(処理結果)
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    resultdb.row_factory = sqlite3.Row

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # メンバー削除
        new_name = f.common.han_to_zen(argument[0])
        if new_name in g.member_list:
            resultdb.execute("delete from member where name=?", (new_name,))
            resultdb.execute("delete from alias where member=?", (new_name,))
            msg = f"「{new_name}」を削除しました。"
            logging.notice(f"remove member: {new_name}")  # type: ignore
        else:
            msg = f"「{new_name}」は登録されていません。"

    if len(argument) == 2:  # 別名削除
        new_name = f.common.han_to_zen(argument[0])
        nic_name = f.common.han_to_zen(argument[1])
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
    read_memberslist()

    return (msg)


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
