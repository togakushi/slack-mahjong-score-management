import re
import configparser

from function import global_value as g
from function import common


def check_namepattern(name):
    """
    登録制限チェック

    Parameters
    ----------
    name : str
        対象文字列（プレイヤー名）
    """

    if len(name) > 8:
        return(False)
    if re.match(r"ゲスト", name): # 登録NGプレイヤー名
        return(False)
    if re.match(r"^(今月|先月|先々月|全部)$", name): # NGワード（サブコマンド引数）
        return(False)
    if re.match(r"^[0-9]{8}$", common.ZEN2HAN(name)): # NGワード（日付形式）
        return(False)
    if re.search("[\\\;:<>,!@#*?/`\"']", name): # 禁則記号
        return(False)
    if not name.isprintable():
        return(False)

    return(True)


def NameReplace(pname, name_replace = True, guest = True):
    """
    表記ブレ修正

    Parameters
    ----------
    name : str
        対象文字列（プレイヤー名）
    """

    pname = re.sub(r"さん$", "", pname)
    pname = common.HAN2ZEN(pname)

    if not name_replace:
        return(pname)

    for player in g.player_list.sections():
        for alias in g.player_list.get(player, "alias").split(","):
            if common.KANA2HIRA(pname) == alias:
                return(player)
            if common.HIRA2KANA(pname) == alias:
                return(player)

    return("ゲスト１" if guest else pname)


def ExsistPlayer(name):
    """
    登録済みメンバーかチェック

    Parameters
    ----------
    name : str
        対象プレイヤー名
    """

    name = NameReplace(name)

    if g.player_list.has_section(name):
        return(name)

    return(False)


def list():
    title = "登録されているメンバー"
    msg = ""

    for player in g.player_list.sections():
        if player == "DEFAULT":
            continue
        alias = g.player_list.get(player, "alias")
        msg += f"{player} -> {alias.split(',')}\n"
    
    return(title, msg)


def Append(v):
    """
    メンバー追加

    Parameters
    ----------
    v : list
        登録プレイヤー名
    """

    if len(v) == 2: # 新規追加
        new_name = common.HAN2ZEN(v[1])
        if g.player_list.has_section(new_name):
            msg = f"「{new_name}」はすでに登録されています。"
        else:
            if len(g.player_list.keys()) > 255: # 登録上限チェック
                msg = f"登録上限を超えています。"
            elif not check_namepattern(new_name):
                msg = f"命名規則に違反しているので登録できません。"
            else:
                g.player_list.add_section(new_name)
                g.player_list.set(new_name, "alias", new_name)
                msg = f"「{new_name}」を登録しました。"

    if len(v) == 3: # 別名登録
        new_name = common.HAN2ZEN(v[1])
        nic_name = common.HAN2ZEN(v[2])
        # ダブりチェック
        checklist = []
        for player in g.player_list.sections():
            checklist.append(player)
            checklist += g.player_list.get(player, "alias").split(",")
        if nic_name in checklist:
            msg = f"「{nic_name}」はすでに登録されています。"
        elif not check_namepattern(nic_name):
            msg = f"命名規則に違反しているので登録できません。"
        else:
            if g.player_list.has_section(new_name):
                alias = g.player_list.get(new_name, "alias")
                if len(alias.split(",")) > 16:
                    msg = f"登録上限を超えています。"
                else:
                    g.player_list.set(new_name, "alias", ",".join([alias, nic_name]))
                    msg = f"「{new_name}」に「{nic_name}」を追加しました。"
            else:
                msg = f"「{new_name}」は登録されていません。"

    return(msg if "msg" in locals() else "使い方が間違っています。")


def Remove(v):
    """
    メンバー削除

    Parameters
    ----------
    v : list
        削除プレイヤー名
    """

    if len(v) == 2: # メンバー削除
        if g.player_list.has_section(v[1]):
            g.player_list.remove_section(v[1])
            msg = f"「{v[1]}」を削除しました。"

    if len(v) == 3: # 別名削除
        if g.player_list.has_section(v[1]):
            alias = g.player_list.get(v[1], "alias").split(",")
            if v[1] == v[2]:
                g.player_list.remove_section(v[1])
                msg = f"「{v[1]}」を削除しました。"
            if v[2] in alias:
                alias.remove(v[2])
                if len(alias) == 0:
                    g.player_list.remove_section(v[1])
                    msg = f"「{v[1]}」を削除しました。"
                else:
                    g.player_list.set(v[1], "alias", ",".join(alias))
                    msg = f"「{v[1]}」から「{v[2]}」を削除しました。"
            else:
                msg = f"「{v[1]}」に「{v[2]}」は登録されていません。"

    return(msg if "msg" in locals() else "使い方が間違っています。")


def configload(configfile):
    config = configparser.ConfigParser()

    try:
        config.read(configfile, encoding="utf-8")
    except:
        sys.exit()

    return(config)


def configsave(config, configfile):
    with open(configfile, "w") as f:
        config.write(f)
