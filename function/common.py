import logging
import re
import unicodedata
import datetime
from dateutil.relativedelta import relativedelta

from function import global_value as g
from goburei import member

logging.basicConfig(level = g.logging_level)


def len_count(text): # 文字数
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return(count)


def HAN2ZEN(text): # 全角変換(数字のみ)
    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(HAN, ZEN)
    return(text.translate(trans_table))


def ZEN2HAN(text): # 半角変換(数字のみ)
    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(ZEN, HAN)
    return(text.translate(trans_table))


def HIRA2KANA(text):
    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(HIRA, KANA)
    return(text.translate(trans_table)) 


def KANA2HIRA(text):
    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(KANA, HIRA)
    return(text.translate(trans_table)) 


def scope_coverage(target_days):
    startday = min(target_days)
    endday = max(target_days)

    try:
        startday = datetime.datetime.fromisoformat(f"{startday[0:4]}-{startday[4:6]}-{startday[6:8]}")
        endday = datetime.datetime.fromisoformat(f"{endday[0:4]}-{endday[4:6]}-{endday[6:8]}") + relativedelta(days = 1)
    except:
        return(False, False)

    return(
        startday.replace(hour = 12, minute = 0, second = 0, microsecond = 0), # starttime
        endday.replace(hour = 11, minute = 59, second = 59, microsecond = 999999), # endtime
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

    currenttime = datetime.datetime.now()
    for keyword in argument:
        if re.match(r"^[0-9]{8}$", keyword):
            try:
                trytime = datetime.datetime.fromisoformat(f"{keyword[0:4]}-{keyword[4:6]}-{keyword[6:8]}")
                target_days.append(trytime.strftime("%Y%m%d"))
            except:
                pass
        if keyword == "当日":
            if currenttime.hour < 12:
                target_days.append((currenttime + relativedelta(days = -1)).strftime("%Y%m%d"))
            else:
                target_days.append(currenttime.strftime("%Y%m%d"))
        if keyword == "今日":
            target_days.append(currenttime.strftime("%Y%m%d"))
        if keyword == "昨日":
            target_days.append((currenttime + relativedelta(days = -1)).strftime("%Y%m%d"))
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
        if member.ExsistPlayer(keyword):
            target_player.append(member.ExsistPlayer(keyword))

        if re.match(r"^ゲスト(なし|ナシ|無し|除外)$", keyword):
            command_option["guest_skip"] = False
            command_option["guest_skip2"] = False
        if re.match(r"^ゲスト(あり|アリ含む)$", keyword):
            command_option["guest_skip"] = True
            command_option["guest_skip2"] = True
        if re.match(r"^(修正|変換)(なし|ナシ|無し)$", keyword):
            command_option["name_replace"] = False
        if re.match(r"^(戦績)$", keyword):
            command_option["results"] = True

    if command_option["recursion"] and len(target_days) == 0:
        command_option["recursion"] = False
        target_days, dummy, dummy = argument_analysis(command_option["default_action"], command_option)

    logging.info(f"[argument_analysis]return: {target_days} {target_player} {command_option}")
    return(target_days, target_player, command_option)
