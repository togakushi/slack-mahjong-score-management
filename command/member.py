import re

import function as f
from function import global_value as g


def check_namepattern(name):
    """
    登録制限チェック

    Parameters
    ----------
    name : str
        対象文字列（プレイヤー名）
    """

    if len(name) > g.config.getint("member", "character_limit"):
        return(False, "登録可能文字数を超えています。")
    if re.match(r"(ゲスト|^[0-9]+$)|DEFAULT", f.translation.ZEN2HAN(name)): # 登録NGプレイヤー名
        return(False, "使用できない名前です。")
    if re.match(r"^((当|今|昨)日|(今|先|先々)月|(今|去)年|全部|最初)$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.match(r"^(戦績|比較|点差|差分|対戦|対戦結果|直近[0-9]+)$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.match(r"^(修正|変換)(なし|ナシ|無し|あり)$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.match(r"^(アーカイブ|一昔|過去|archive)$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.match(r"^(詳細|verbose)$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.match(r"^(トップ|上位|top)[0-9]+$", name): # NGワード（サブコマンド引数）
        return(False, "コマンドに使用される単語は登録できません。")
    if re.search("[\\\;:<>,!@#*?/`\"']", name): # 禁則記号
        return(False, "使用できない記号が含まれています。")
    if name == g.guest_name:
        return(False, "使用できない名前です。")
    if not name.isprintable():
        return(False, "使用できない記号が含まれています。")

    return(True, "OK")


def NameReplace(pname, command_option):
    """
    表記ブレ修正(正規化)

    Parameters
    ----------
    pname : str
        対象文字列（プレイヤー名）

    command_option : dict
        コマンドオプション

    Returns
    -------
    pname : str
        表記ブレ修正後のプレイヤー名
    """

    pname = re.sub(r"さん$", "", f.translation.HAN2ZEN(pname))

    if not command_option["playername_replace"]:
        return(pname)

    break_flg = False
    for player in g.player_list.sections():
        if break_flg:
            break
        for alias in g.player_list.get(player, "alias").split(","):
            if alias in [f.translation.KANA2HIRA(pname), f.translation.HIRA2KANA(pname)]:
                pname = player
                break_flg = True
                break

    if not command_option["unregistered_replace"]:
      if not ExsistPlayer(pname):
        pname = pname + "(※)"
    else:
      if not ExsistPlayer(pname):
        pname = g.guest_name

    return(pname)


def ExsistPlayer(name):
    """
    登録済みメンバーかチェック

    Parameters
    ----------
    name : str
        対象プレイヤー名(正規化後)

    Returns
    -------
    bool : False
    name : str
    """

    command_option = {
        "playername_replace": True,
        "unregistered_replace": True,
    }

    if g.player_list.has_section(name):
        return(name)

    return(False)


def GetMemberName(myname = None):
    ret = []
    for player in g.player_list.sections():
        if player == "DEFAULT":
            continue
        ret.append(player)

    if myname in ret:
        ret.remove(myname)

    return(ret)


def CountPadding(data):
    """
    """
    name_list = []

    if type(data) is list:
        name_list = data

    if type(data) is dict:
        for i in data.keys():
            for name in [data[i][x]["name"] for x in ("東家", "南家", "西家", "北家")]:
                if name not in name_list:
                    name_list.append(name)

    if name_list:
        return(max([f.translation.len_count(x) for x in name_list]))
    else:
        return(0)


def GetList():
    title = "登録されているメンバー"
    msg = ""

    for player in g.player_list.sections():
        if player == "DEFAULT":
            continue
        alias = g.player_list.get(player, "alias")
        msg += f"{player} -> {alias.split(',')}\n"
    
    return(title, msg)


def Append(argument):
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

    ret = False
    msg = "使い方が間違っています。"

    if len(argument) == 1: # 新規追加
        new_name = f.translation.HAN2ZEN(argument[0])

        if g.player_list.has_section(new_name):
            msg = f"「{new_name}」はすでに登録されています。"
        else:
            if len(g.player_list.keys()) > g.config.getint("member", "registration_limit"):
                msg = f"登録上限を超えています。"

            ret, msg = check_namepattern(new_name)
            if ret:
                g.player_list.add_section(new_name)
                g.player_list.set(new_name, "alias", new_name)
                msg = f"「{new_name}」を登録しました。"

    if len(argument) == 2: # 別名登録
        new_name = f.translation.HAN2ZEN(argument[0])
        nic_name = f.translation.HAN2ZEN(argument[1])

        # ダブりチェック
        checklist = []
        for player in g.player_list.sections():
            checklist.append(player)
            checklist += g.player_list.get(player, "alias").split(",")

        if nic_name in checklist:
            msg = f"「{nic_name}」はすでに登録されています。"

        ret, msg = check_namepattern(nic_name)
        if ret:
            if g.player_list.has_section(new_name):
                alias = g.player_list.get(new_name, "alias")
                if len(alias.split(",")) > int(g.config.get("member", "alias_limit")):
                    msg = f"登録上限を超えています。"
                else:
                    g.player_list.set(new_name, "alias", ",".join([alias, nic_name]))
                    msg = f"「{new_name}」に「{nic_name}」を追加しました。"
            else:
                msg = f"「{new_name}」はまだ登録されていません。"

    return(msg)


def Remove(argument):
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

    msg = "使い方が間違っています。"

    if len(argument) == 1: # メンバー削除
        new_name = f.translation.HAN2ZEN(argument[0])

        if g.player_list.has_section(new_name):
            g.player_list.remove_section(new_name)
            msg = f"「{new_name}」を削除しました。"

    if len(argument) == 2: # 別名削除
        new_name = f.translation.HAN2ZEN(argument[0])
        new_name = f.translation.HAN2ZEN(argument[1])

        if g.player_list.has_section(new_name):
            alias = g.player_list.get(new_name, "alias").split(",")

            if new_name == new_name:
                g.player_list.remove_section(new_name)
                msg = f"「{new_name}」を削除しました。"

            if new_name in alias:
                alias.remove(new_name)
                if len(alias) == 0:
                    g.player_list.remove_section(new_name)
                    msg = f"「{new_name}」を削除しました。"
                else:
                    g.player_list.set(new_name, "alias", ",".join(alias))
                    msg = f"「{new_name}」から「{new_name}」を削除しました。"
            else:
                msg = f"「{new_name}」に「{new_name}」は登録されていません。"

    return(msg)
