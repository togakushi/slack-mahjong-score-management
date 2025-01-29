import logging
import re
import sqlite3

import global_value as g
from cls.parameter import command_option
from lib import command as c
from lib import database as d
from lib import function as f


def read_memberslist(log=True):
    """
    メンバー/チームリスト読み込み
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    rows = resultdb.execute("select name from member where id=0")
    g.prm.guest_name = rows.fetchone()[0]

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
        logging.notice(f"guest_name: {g.prm.guest_name}")
        logging.notice(f"member_list: {set(g.member_list.values())}")
        logging.notice(f"team_list: {[x['team'] for x in g.team_list]}")


def name_replace(pname, add_mark=False):
    """
    表記ブレ修正(正規化)

    Parameters
    ----------
    pname : str
        対象文字列（プレイヤー名）

    Returns
    -------
    name : str
        表記ブレ修正後のプレイヤー名
    """

    pname = f.common.han_to_zen(pname)
    check_list = list(set(g.member_list.keys()))

    if pname in check_list:
        return (g.member_list[pname])

    # 敬称削除
    honor = r"(くん|さん|ちゃん|クン|サン|チャン|君)$"
    if re.match(fr".*{honor}", pname):
        if not re.match(fr".*(っ|ッ){honor}", pname):
            pname = re.sub(fr"{honor}", "", pname)
    if pname in check_list:
        return (g.member_list[pname])

    # ひらがな、カタカナでチェック
    if f.common.kata_to_hira(pname) in check_list:
        return (g.member_list[f.common.kata_to_hira(pname)])
    if f.common.hira_to_kana(pname) in check_list:
        return (g.member_list[f.common.hira_to_kana(pname)])

    # メンバーリストに見つからない場合
    if g.opt.unregistered_replace:
        return (g.prm.guest_name)
    else:
        if add_mark:
            return (f"{pname}({g.cfg.setting.guest_mark})")
        else:
            return (pname)


def count_padding(data):
    """
    """
    name_list = []

    if type(data) is list:
        name_list = data

    if type(data) is dict:
        for i in data.keys():
            for name in [data[i][x]["name"] for x in g.wind[0:4]]:
                if name not in name_list:
                    name_list.append(name)

    if name_list:
        return (max([f.common.len_count(x) for x in name_list]))
    else:
        return (0)


def get_members_list():
    """
    登録済みのメンバー一覧をslackに出力する
    """

    title = "登録済みメンバー一覧"
    padding = c.member.count_padding(list(set(g.member_list.values())))
    msg = "# 表示名{}： 登録されている名前 #\n".format(" " * (padding - 8))

    for pname in set(g.member_list.values()):
        name_list = []
        for alias in g.member_list.keys():
            if g.member_list[alias] == pname:
                name_list.append(alias)
        msg += "{}{}： {}\n".format(
            pname,
            " " * (padding - f.common.len_count(pname)),
            ", ".join(name_list),
        )

    return (title, msg)


def member_info(name):
    """
    指定メンバーの記録情報を返す
    """

    sql = """
        select
            count() as game_count,
            min(ts) as first_game,
            max(ts) as last_game,
            max(rpoint) as max_rpoint,
            min(rpoint) as min_rpoint
        from
            individual_results
        where
            rule_version = ?
            and name = ?
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(sql, (g.prm.rule_version, name))
    ret = dict(rows.fetchone())
    resultdb.close()

    return (ret)


def member_append(argument):
    """
    メンバー追加

    Parameters
    ----------
    argument : list
        argument[0] = 登録するプレイヤー名
        argument[1] = 登録する別名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    resultdb = sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = False
    dbupdate_flg = False
    msg = "使い方が間違っています。"

    if len(argument) == 1:  # 新規追加
        new_name = f.common.han_to_zen(argument[0])
        logging.notice(f"new member: {new_name}")

        rows = resultdb.execute("select count() from member")
        count = rows.fetchone()[0]
        if count > g.cfg.config["member"].getint("registration_limit", 255):
            msg = "登録上限を超えています。"
        else:  # 登録処理
            ret, msg = check_namepattern(new_name)
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

    if len(argument) == 2:  # 別名登録
        new_name = f.common.han_to_zen(argument[0])
        nic_name = f.common.han_to_zen(argument[1])
        logging.notice(f"alias: {new_name} -> {nic_name}")

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
            ret, msg = check_namepattern(nic_name)
            if ret:
                resultdb.execute("insert into alias(name, member) values (?,?)", (nic_name, new_name))
                msg = f"「{new_name}」に「{nic_name}」を追加しました。"
                dbupdate_flg = True

        if dbupdate_flg:
            rows = resultdb.execute(
                """select count() from (
                        select p1_name as name from result
                        union all select p2_name from result
                        union all select p3_name from result
                        union all select p4_name from result
                        union all select name from remarks
                    )
                    where name in (?, ?, ?)
                    group by name
                """, (nic_name, f.common.kata_to_hira(nic_name), f.common.hira_to_kana(nic_name)))
            count = rows.fetchone()[0]
            if count != 0:  # 過去成績更新
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
    """
    メンバー削除

    Parameters
    ----------
    argument : list
        argument[0] = 削除するプレイヤー名
        argument[1] = 削除する別名

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    resultdb.row_factory = sqlite3.Row

    msg = "使い方が間違っています。"

    if len(argument) == 1:  # メンバー削除
        new_name = f.common.han_to_zen(argument[0])
        logging.notice(f"remove member: {new_name}")

        if new_name in g.member_list:
            resultdb.execute("delete from member where name=?", (new_name,))
            resultdb.execute("delete from alias where member=?", (new_name,))
            msg = f"「{new_name}」を削除しました。"
        else:
            msg = f"「{new_name}」は登録されていません。"

    if len(argument) == 2:  # 別名削除
        new_name = f.common.han_to_zen(argument[0])
        nic_name = f.common.han_to_zen(argument[1])
        logging.notice(f"alias remove: {new_name} -> {nic_name}")

        if nic_name in g.member_list:
            resultdb.execute(
                "delete from alias where name=? and member=?",
                (nic_name, new_name)
            )
            msg = f"「{new_name}」から「{nic_name}」を削除しました。"
        else:
            msg = f"「{new_name}」に「{nic_name}」は登録されていません。"

    resultdb.commit()
    resultdb.close()
    read_memberslist()

    return (msg)


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

    # 登録済みメンバーかチェック
    check_list = list(g.member_list.keys())
    check_list += [f.common.kata_to_hira(i) for i in g.member_list.keys()]  # ひらがな
    check_list += [f.common.hira_to_kana(i) for i in g.member_list.keys()]  # カタカナ
    if name in check_list:
        return (False, f"「{name}」はすでに使用されています。")

    # 登録規定チェック
    if len(name) > g.cfg.config["member"].getint("character_limit", 8):  # 文字制限
        return (False, "登録可能文字数を超えています。")
    if name == g.prm.guest_name:  # 登録NGプレイヤー名
        return (False, "使用できない名前です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        return (False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    if g.search_word.find(name):
        return (False, "検索範囲指定に使用される単語は登録できません。")

    chk = command_option()
    chk.check([name])
    if vars(chk):
        return (False, "オプションに使用される単語は登録できません。")

    if name in g.cfg.word_list():
        return (False, "コマンドに使用される単語は登録できません。")

    return (True, "OK")
