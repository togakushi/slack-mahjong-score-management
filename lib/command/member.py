import re
import sqlite3
from itertools import chain

import lib.function as f
import lib.command as c
import lib.database as d
from lib.function import global_value as g


def read_memberslist():
    """
    メンバー/チームリスト読み込み
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    rows = resultdb.execute("select name from member where id=0")
    g.guest_name = rows.fetchone()[0]

    rows = resultdb.execute("select name, member from alias")
    g.member_list = dict(rows.fetchall())

    rows = resultdb.execute("select * from team")
    g.team_list = dict(rows.fetchall())

    resultdb.close()

    g.logging.notice(f"guest_name: {g.guest_name}") # type: ignore
    g.logging.notice(f"member_list: {set(g.member_list.values())}") # type: ignore
    g.logging.notice(f"team_list: {list(g.team_list.values())}") # type: ignore


def NameReplace(pname, add_mark = False):
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

    pname = f.common.HAN2ZEN(pname)
    check_list = list(set(g.member_list.keys()))

    if pname in check_list:
        return(g.member_list[pname])

    # 敬称削除
    honor = r"(くん|さん|ちゃん|クン|サン|チャン|君)$"
    if re.match(fr".*{honor}", pname):
        if not re.match(fr".*(っ|ッ){honor}", pname):
            pname = re.sub(fr"{honor}", "", pname)
    if pname in check_list:
        return(g.member_list[pname])

    # ひらがな、カタカナでチェック
    if f.common.KANA2HIRA(pname) in check_list:
        return(g.member_list[f.common.KANA2HIRA(pname)])
    if f.common.HIRA2KANA(pname) in check_list:
        return(g.member_list[f.common.HIRA2KANA(pname)])

    # メンバーリストに見つからない場合
    if g.opt.unregistered_replace:
        return(g.guest_name)
    else:
        if add_mark:
            return(f"{pname}({g.guest_mark})")
        else:
            return(pname)


def CountPadding(data):
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
        return(max([f.common.len_count(x) for x in name_list]))
    else:
        return(0)


def Getmemberslist():
    """
    登録済みのメンバー一覧をslackに出力する
    """

    title = "登録済みメンバー一覧"
    padding = c.member.CountPadding(list(set(g.member_list.values())))
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

    return(title, msg)


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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(sql, (g.rule_version, name))
    ret = dict(rows.fetchone())
    resultdb.close()

    return(ret)


def MemberAppend(argument):
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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = False
    dbupdate_flg = False
    msg = "使い方が間違っています。"

    if len(argument) == 1: # 新規追加
        new_name = f.common.HAN2ZEN(argument[0])
        g.logging.notice(f"new member: {new_name}") # type: ignore

        rows = resultdb.execute("select count() from member")
        count = rows.fetchone()[0]
        if count > g.config["member"].getint("registration_limit", 255):
            msg = f"登録上限を超えています。"
        else: # 登録処理
            ret, msg = check_namepattern(new_name)
            if ret:
                resultdb.execute(f"insert into member(name) values (?)", (new_name,))
                resultdb.execute(f"insert into alias(name, member) values (?,?)", (new_name, new_name))
                msg = f"「{new_name}」を登録しました。"

    if len(argument) == 2: # 別名登録
        new_name = f.common.HAN2ZEN(argument[0])
        nic_name = f.common.HAN2ZEN(argument[1])
        g.logging.notice(f"alias: {new_name} -> {nic_name}") # type: ignore

        registration_flg = True
        rows = resultdb.execute("select count() from alias where member=?", (new_name,))
        count = rows.fetchone()[0]
        if count == 0:
            msg = f"「{new_name}」はまだ登録されていません。"
            registration_flg = False
        if count > g.config["member"].getint("alias_limit", 16):
            msg = f"登録上限を超えています。"
            registration_flg = False

        if registration_flg: # 登録処理
            ret, msg = check_namepattern(nic_name)
            if ret:
                resultdb.execute("insert into alias(name, member) values (?,?)", (nic_name, new_name))
                msg = f"「{new_name}」に「{nic_name}」を追加しました。"
                dbupdate_flg = True

        if dbupdate_flg:
            rows = resultdb.execute(
                """select count() from result
                    where ? in (p1_name, p2_name, p3_name, p4_name)
                    or ? in (p1_name, p2_name, p3_name, p4_name)
                    or ? in (p1_name, p2_name, p3_name, p4_name)
                """, (nic_name, f.common.KANA2HIRA(nic_name), f.common.HIRA2KANA(nic_name)))
            count = rows.fetchone()[0]
            if count != 0: # 過去成績更新
                msg += d.common.database_backup()
                for col in ("p1_name", "p2_name", "p3_name", "p4_name"):
                    resultdb.execute(f"update result set {col}=? where {col}=?", (new_name, nic_name))
                    resultdb.execute(f"update result set {col}=? where {col}=?", (new_name, f.common.KANA2HIRA(nic_name)))
                    resultdb.execute(f"update result set {col}=? where {col}=?", (new_name, f.common.HIRA2KANA(nic_name)))
                msg += "\nデータベースを更新しました。"

    resultdb.commit()
    resultdb.close()
    read_memberslist()

    return(msg)


def MemberRemove(argument):
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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    msg = "使い方が間違っています。"

    if len(argument) == 1: # メンバー削除
        new_name = f.common.HAN2ZEN(argument[0])
        g.logging.notice(f"remove member: {new_name}") # type: ignore

        if new_name in g.member_list:
            resultdb.execute("delete from member where name=?", (new_name,))
            resultdb.execute("delete from alias where member=?",(new_name,))
            msg = f"「{new_name}」を削除しました。"
        else:
            msg = f"「{new_name}」は登録されていません。"

    if len(argument) == 2: # 別名削除
        new_name = f.common.HAN2ZEN(argument[0])
        nic_name = f.common.HAN2ZEN(argument[1])
        g.logging.notice(f"alias remove: {new_name} -> {nic_name}") # type: ignore

        if nic_name in g.member_list:
            resultdb.execute("delete from alias where name=? and member=?",(nic_name, new_name))
            msg = f"「{new_name}」から「{nic_name}」を削除しました。"
        else:
            msg = f"「{new_name}」に「{nic_name}」は登録されていません。"

    resultdb.commit()
    resultdb.close()
    read_memberslist()

    return(msg)


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
    check_list += [f.common.KANA2HIRA(i) for i in g.member_list.keys()] # ひらがな
    check_list += [f.common.HIRA2KANA(i) for i in g.member_list.keys()] # カタカナ
    if name in check_list:
        return(False, f"「{name}」はすでに使用されています。")

    # 登録規定チェック
    if len(name) > g.config["member"].getint("character_limit", 8): # 文字制限
        return(False, "登録可能文字数を超えています。")
    if name == g.guest_name: # 登録NGプレイヤー名
        return(False, "使用できない名前です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable(): # 禁則記号
        return(False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    chk = g.command_option()
    chk.check([name])
    if vars(chk):
        return(False, "日付、またはオプションに使用される単語は登録できません。")

    commandlist = list(g.commandword.values())
    commandlist.extend([g.config["setting"].get("slash_commandname")])
    commandlist.extend([g.config["setting"].get("remarks_word")])
    commandlist.extend([g.config["search"].get("keyword")])
    commandlist.extend([x for x, _ in g.config.items("alias")])
    commandlist.extend(chain.from_iterable([y.split(",") for _, y in g.config.items("alias")]))
    if name in set(commandlist):
        return(False, "コマンドに使用される単語は登録できません。")

    return(True, "OK")
