import configparser
import re
import sys
import unicodedata
from datetime import datetime

from dateutil.relativedelta import relativedelta

import command as c
from function import global_value as g


def configload(configfile):
    config = configparser.ConfigParser()

    try:
        config.read(configfile, encoding="utf-8")
    except:
        sys.exit()

    g.logging.info(f"configload: {configfile} -> {config.sections()}")
    return(config)


def configsave(config, configfile):
    with open(configfile, "w") as f:
        config.write(f)


def scope_coverage(target_days):
    startday = min(target_days)
    endday = max(target_days)

    try:
        startday = datetime.fromisoformat(f"{startday[0:4]}-{startday[4:6]}-{startday[6:8]}")
        endday = datetime.fromisoformat(f"{endday[0:4]}-{endday[4:6]}-{endday[6:8]}") + relativedelta(days = 1)
    except:
        return(False, False)

    return(
        startday.replace(hour = 12, minute = 0, second = 0, microsecond = 0), # starttime
        endday.replace(hour = 11, minute = 59, second = 59, microsecond = 0), # endtime
    )


def argument_analysis(argument, command_option):
    """
    引数の内容を解析し、日付とプレイヤー名を返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数
        集計対象の期間などが指定される

    command_option : dict
        コマンドオプション

    Returns
    -------
    target_days : list
        キーワードで指定された日付範囲を格納

    target_player : list
        キーワードから見つかったプレイヤー名を格納

    command_option : dict
        更新されたコマンドオプション
    """

    target_days = []
    target_player = []

    currenttime = datetime.now() + relativedelta(hours = -12)
    for keyword in argument:
        # 日付取得
        if re.match(r"^[0-9]{8}$", keyword):
            try:
                trytime = datetime.fromisoformat(f"{keyword[0:4]}-{keyword[4:6]}-{keyword[6:8]}")
                target_days.append(trytime.strftime("%Y%m%d"))
            except:
                pass
        if keyword == "当日":
            target_days.append(currenttime.strftime("%Y%m%d"))
        if keyword == "今日":
            target_days.append(datetime.now().strftime("%Y%m%d"))
        if keyword == "昨日":
            target_days.append((datetime.now() + relativedelta(days = -1)).strftime("%Y%m%d"))
        if keyword == "今月":
            target_days.append((currenttime + relativedelta(day = 1, months = 0)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = 1, days = -1,)).strftime("%Y%m%d"))
        if keyword == "先月":
            target_days.append((currenttime + relativedelta(day = 1, months = -1)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = 0, days = -1,)).strftime("%Y%m%d"))
        if keyword == "先々月":
            target_days.append((currenttime + relativedelta(day = 1, months = -2)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = -1, days = -1,)).strftime("%Y%m%d"))
        if keyword == "全部":
            target_days.append((currenttime + relativedelta(days = -91)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(days = 1)).strftime("%Y%m%d"))
        if keyword == "最初":
            target_days.append((currenttime + relativedelta(days = -91)).strftime("%Y%m%d"))
        if c.member.ExsistPlayer(keyword):
            target_player.append(c.member.ExsistPlayer(keyword))

        # コマンドオプションフラグ変更
        if re.match(r"^ゲスト(なし|ナシ)$", keyword):
            command_option["guest_skip"] = False
            command_option["guest_skip2"] = False
        if re.match(r"^ゲスト(あり|アリ)$", keyword):
            command_option["guest_skip"] = True
            command_option["guest_skip2"] = True
        if re.match(r"^ゲスト無効$", keyword):
            command_option["unregistered_replace"] = False
        if re.match(r"^(修正|変換)(なし|ナシ)$", keyword):
            command_option["playername_replace"] = False
        if re.match(r"^(比較|点差|差分)$", keyword):
            command_option["score_comparisons"] = True
        if re.match(r"^(戦績)$", keyword):
            command_option["game_results"] = True
        if re.match(r"^(アーカイブ|一昔|archive)$", keyword):
            command_option["archive"] = True

    if command_option["recursion"] and len(target_days) == 0:
        command_option["recursion"] = False
        target_days, dummy, dummy = argument_analysis(command_option["aggregation_range"], command_option)

    g.logging.info(f"[argument_analysis]return: {target_days} {target_player} {command_option}")
    return(target_days, target_player, command_option)


def command_option_initialization(command):
    """
    設定ファイルからコマンドのオプションのデフォルト値を読み込む

    Parameters
    ----------
    command : str
        読み込むコマンド名

    Returns
    -------
    option : dict
        初期化されたオプション
    """

    option = {
        "aggregation_range": [],
        "recursion": True,
    }

    option["aggregation_range"].append(g.config[command].get("aggregation_range", "当日"))
    option["playername_replace"] = g.config[command].getboolean("playername_replace", True)
    option["unregistered_replace"] = g.config[command].getboolean("unregistered_replace", True)
    option["guest_skip"] = g.config[command].getboolean("guest_skip", True)
    option["guest_skip2"] = g.config[command].getboolean("guest_skip2", True)
    option["score_comparisons"] = g.config[command].getboolean("score_comparisons", False)
    option["archive"] = g.config[command].getboolean("archive", False) 
    option["game_results"] = g.config[command].getboolean("game_results", False)

    return(option)


def parameter_load():
    # メンバー登録ファイル
    if g.args.member:
        g.memberfile = g.args.member
    else:
        g.memberfile = g.config["member"].get("filename", "member.ini")

    try:
        g.player_list = configparser.ConfigParser()
        g.player_list.read(g.memberfile, encoding="utf-8")
        g.logging.info(f"configload: {g.memberfile} -> {g.player_list.sections()}")
    except:
        sys.exit(f"{g.memberfile}: file not found")

    g.guest_name = g.config["member"].get("guest_name", "ゲスト")
    g.dbfile = g.config["database"].get("filename", "score.db")
