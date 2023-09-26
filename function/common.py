import re
import sys
import unicodedata
from datetime import datetime

from dateutil.relativedelta import relativedelta

import command as c
from function import global_value as g


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

    target_count : int
        集計するゲーム数

    command_option : dict
        更新されたコマンドオプション
    """

    target_days = []
    target_player = []
    target_count = 0

    currenttime = datetime.now()
    for keyword in argument:
        # 日付取得
        if re.match(r"^[0-9]{8}$", keyword):
            try:
                trytime = datetime.fromisoformat(f"{keyword[0:4]}-{keyword[4:6]}-{keyword[6:8]}")
                target_days.append(trytime.strftime("%Y%m%d"))
                continue
            except:
                continue
        if keyword == "当日":
            target_days.append((currenttime + relativedelta(hours = -12)).strftime("%Y%m%d"))
            continue
        if keyword == "今日":
            target_days.append(currenttime.strftime("%Y%m%d"))
            continue
        if keyword == "昨日":
            target_days.append((currenttime + relativedelta(days = -1)).strftime("%Y%m%d"))
            continue
        if keyword == "今月":
            target_days.append((currenttime + relativedelta(day = 1, months = 0)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = 1, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "先月":
            target_days.append((currenttime + relativedelta(day = 1, months = -1)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = 0, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "先々月":
            target_days.append((currenttime + relativedelta(day = 1, months = -2)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 1, months = -1, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "去年":
            target_days.append((currenttime + relativedelta(day = 1, month = 1, years = -1)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 31, month = 12, years = -1)).strftime("%Y%m%d"))
            continue
        if keyword == "今年":
            target_days.append((currenttime + relativedelta(day = 1, month = 1)).strftime("%Y%m%d"))
            target_days.append((currenttime + relativedelta(day = 31, month = 12)).strftime("%Y%m%d"))
            continue
        if keyword == "最初":
            target_days.append((currenttime + relativedelta(days = -91)).strftime("%Y%m%d"))
            continue
        if keyword == "最後":
            target_days.append((currenttime + relativedelta(days = 1)).strftime("%Y%m%d"))
            continue
        if keyword == "全部":
            target_days.append("20200101")
            target_days.append("20301231")
            continue

        # コマンドオプションフラグ変更
        if re.match(r"^ゲスト(なし|ナシ|無し)$", keyword):
            command_option["guest_skip"] = False
            command_option["guest_skip2"] = False
            continue
        if re.match(r"^ゲスト(あり|アリ)$", keyword):
            command_option["guest_skip"] = True
            command_option["guest_skip2"] = True
            continue
        if re.match(r"^ゲスト無効$", keyword):
            command_option["unregistered_replace"] = False
            continue
        if re.match(r"^(修正|変換)(なし|ナシ|無し)$", keyword):
            command_option["playername_replace"] = False
            continue
        if re.match(r"^(全員|all)$", keyword):
            command_option["all_member"] = True
            continue
        if re.match(r"^(比較|点差|差分)$", keyword):
            command_option["score_comparisons"] = True
            continue
        if re.match(r"^(戦績)$", keyword):
            command_option["game_results"] = True
            continue
        if re.match(r"^(対戦|対戦結果)$", keyword):
            command_option["versus_matrix"] = True
            continue
        if re.match(r"^(詳細|verbose)$", keyword):
            command_option["verbose"] = True
            continue
        if re.match(r"^(アーカイブ|一昔|過去|archive)$", keyword):
            command_option["archive"] = True
            continue
        if re.match(r"^(直近)([0-9]+)$", keyword):
            target_count = int(re.sub(rf"^(直近)([0-9]+)$", r"\2", keyword))
            continue
        if re.match(r"^(トップ|上位|top)([0-9]+)$", keyword):
            command_option["ranked"] = int(re.sub(rf"^(トップ|上位|top)([0-9]+)$", r"\2", keyword))
            continue

        # プレイヤー名
        target_player.append(c.member.NameReplace(keyword, command_option))

    if command_option["recursion"] and len(target_days) == 0:
        command_option["recursion"] = False
        target_days, dummy, dummy, dummy = argument_analysis(command_option["aggregation_range"], command_option)

    g.logging.info(f"[argument_analysis]return: {target_days} {target_player} {target_count} {command_option}")
    return(target_days, target_player, target_count, command_option)
