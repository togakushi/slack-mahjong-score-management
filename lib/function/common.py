import re
from datetime import datetime
from itertools import chain

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def scope_coverage(target_days):
    """
    日付リストから期間(最小値と最大値)を返す

    Parameters
    ----------
    target_days : list

    Returns
    -------
    startday : datetime
        最小日

    endday : datetime
        最大日
    """
    startday = min(target_days)
    endday = max(target_days)

    try:
        startday = datetime.fromisoformat(f"{startday[0:4]}-{startday[4:6]}-{startday[6:8]}")
        endday = datetime.fromisoformat(f"{endday[0:4]}-{endday[4:6]}-{endday[6:8]}") + relativedelta(days = 1)
    except:
        return(False, False)

    return(
        startday.replace(hour = 12, minute = 0, second = 0, microsecond = 0), # starttime
        endday.replace(hour = 11, minute = 59, second = 59, microsecond = 999999), # endtime
    )


def argument_analysis(argument, command_option = {}):
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

    current_time = datetime.now()
    appointed_time = current_time + relativedelta(hours = -12)
    for keyword in argument:
        # 日付取得
        if re.match(r"^[0-9]{8}$", keyword):
            try:
                trytime = datetime.fromisoformat(f"{keyword[0:4]}-{keyword[4:6]}-{keyword[6:8]}")
                target_days.append(trytime.strftime("%Y%m%d"))
                continue
            except: # 日付変換できない数値は無視
                continue
        if keyword == "当日":
            target_days.append(appointed_time.strftime("%Y%m%d"))
            continue
        if keyword == "今日":
            target_days.append(current_time.strftime("%Y%m%d"))
            continue
        if keyword == "昨日":
            target_days.append((current_time + relativedelta(days = -1)).strftime("%Y%m%d"))
            continue
        if keyword == "今月":
            target_days.append((appointed_time + relativedelta(day = 1, months = 0)).strftime("%Y%m%d"))
            target_days.append((appointed_time + relativedelta(day = 1, months = 1, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "先月":
            target_days.append((appointed_time + relativedelta(day = 1, months = -1)).strftime("%Y%m%d"))
            target_days.append((appointed_time + relativedelta(day = 1, months = 0, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "先々月":
            target_days.append((appointed_time + relativedelta(day = 1, months = -2)).strftime("%Y%m%d"))
            target_days.append((appointed_time + relativedelta(day = 1, months = -1, days = -1,)).strftime("%Y%m%d"))
            continue
        if keyword == "今年":
            target_days.append((current_time + relativedelta(day = 1, month = 1)).strftime("%Y%m%d"))
            target_days.append((current_time + relativedelta(day = 31, month = 12)).strftime("%Y%m%d"))
            continue
        if keyword in ("去年", "昨年"):
            target_days.append((current_time + relativedelta(day = 1, month = 1, years = -1)).strftime("%Y%m%d"))
            target_days.append((current_time + relativedelta(day = 31, month = 12, years = -1)).strftime("%Y%m%d"))
            continue
        if keyword == "一昨年":
            target_days.append((current_time + relativedelta(day = 1, month = 1, years = -2)).strftime("%Y%m%d"))
            target_days.append((current_time + relativedelta(day = 31, month = 12, years = -2)).strftime("%Y%m%d"))
            continue
        if keyword == "最後":
            target_days.append((current_time + relativedelta(days = 1)).strftime("%Y%m%d"))
            continue
        if keyword == "全部":
            target_days.append("20200101")
            target_days.append((current_time + relativedelta(days = 1)).strftime("%Y%m%d"))
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
        if re.match(r"^(全員|all)$", keyword):
            command_option["all_player"] = True
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
        if re.match(r"^(順位)$", keyword):
            command_option["order"] = True
            continue
        if re.match(r"^(統計)$", keyword):
            command_option["statistics"] = True
            continue
        if re.match(r"^(個人|個人成績)$", keyword):
            command_option["personal"] = True
            continue
        if re.match(r"^(直近)([0-9]+)$", keyword):
            target_count = int(re.sub(rf"^(直近)([0-9]+)$", r"\2", keyword))
            continue
        if re.match(r"^(トップ|上位|top)([0-9]+)$", keyword):
            command_option["ranked"] = int(re.sub(rf"^(トップ|上位|top)([0-9]+)$", r"\2", keyword))
            continue
        if re.match(r"^(規定数|規定打数)([0-9]+)$", keyword):
            command_option["stipulated"] = int(re.sub(rf"^(規定数|規定打数)([0-9]+)$", r"\2", keyword))
            continue

        # どのオプションにもマッチしないものはプレイヤー名
        target_player.append(c.member.NameReplace(keyword, command_option))

    # 日付再取得のために再帰呼び出し
    if command_option.get("recursion") and not target_days:
        if "aggregation_range" in command_option:
            command_option["recursion"] = False # ループ防止
            target_days, _, _, _ = argument_analysis(command_option["aggregation_range"], command_option)
            command_option["recursion"] = True # 元に戻す

    g.logging.info(f"return: target_days: {target_days} target_count: {target_count}")
    g.logging.info(f"return: target_player: {target_player}")
    g.logging.info(f"return: command_option: {command_option}")
    return(target_days, target_player, target_count, command_option)


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
    check_list += [f.translation.KANA2HIRA(i) for i in g.member_list.keys()] # ひらがな
    check_list += [f.translation.HIRA2KANA(i) for i in g.member_list.keys()] # カタカナ
    if name in check_list:
        return(False, f"「{name}」はすでに使用されています。")

    # 登録規定チェック
    if len(name) > g.config["member"].getint("character_limit", 8): # 文字制限
        return(False, "登録可能文字数を超えています。")
    if name == g.guest_name: # 登録NGプレイヤー名
        return(False, "使用できない名前です。")
    if re.search("[\\;:<>,!@#*?/`\"']", name) or not name.isprintable(): # 禁則記号
        return(False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    chk_target_days, _, _, chk_command_option = f.common.argument_analysis([name])
    if chk_target_days:
        return(False, "検索範囲指定に使用される単語は登録できません。")
    if chk_command_option:
        return(False, "オプションに使用される単語は登録できません。")

    commandlist = list(g.commandword.values())
    commandlist.extend([g.config["setting"].get("slash_commandname")])
    commandlist.extend([g.config["setting"].get("remarks_word")])
    commandlist.extend([g.config["search"].get("keyword")])
    commandlist.extend([x for x, _ in g.config.items("alias")])
    commandlist.extend(chain.from_iterable([y.split(",") for _, y in g.config.items("alias")]))
    if name in set(commandlist):
        return(False, "コマンドに使用される単語は登録できません。")

    return(True, "OK")
