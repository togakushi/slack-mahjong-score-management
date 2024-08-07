import os
import re
import unicodedata
from datetime import datetime

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
import lib.database as d
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
        return(datetime.now(), datetime.now())

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
        match keyword.lower():
            # 日付取得
            case keyword if re.match(r"^([0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{4}/[0-9]{2}/[0-9]{2})$", keyword):
                try:
                    trystr = re.sub("[/-]", "", keyword)
                    trytime = datetime.fromisoformat(f"{trystr[0:4]}-{trystr[4:6]}-{trystr[6:8]}")
                    target_days.append(trytime.strftime("%Y%m%d"))
                except: # 日付変換できない数値は無視
                    pass
            case "当日":
                target_days.append(appointed_time.strftime("%Y%m%d"))
            case "今日":
                target_days.append(current_time.strftime("%Y%m%d"))
            case "昨日":
                target_days.append((current_time + relativedelta(days = -1)).strftime("%Y%m%d"))
            case "今月":
                target_days.append((appointed_time + relativedelta(day = 1, months = 0)).strftime("%Y%m%d"))
                target_days.append((appointed_time + relativedelta(day = 1, months = 1, days = -1,)).strftime("%Y%m%d"))
            case "先月":
                target_days.append((appointed_time + relativedelta(day = 1, months = -1)).strftime("%Y%m%d"))
                target_days.append((appointed_time + relativedelta(day = 1, months = 0, days = -1,)).strftime("%Y%m%d"))
            case "先々月":
                target_days.append((appointed_time + relativedelta(day = 1, months = -2)).strftime("%Y%m%d"))
                target_days.append((appointed_time + relativedelta(day = 1, months = -1, days = -1,)).strftime("%Y%m%d"))
            case "今年":
                target_days.append((current_time + relativedelta(day = 1, month = 1)).strftime("%Y%m%d"))
                target_days.append((current_time + relativedelta(day = 31, month = 12)).strftime("%Y%m%d"))
            case "去年" | "昨年":
                target_days.append((current_time + relativedelta(day = 1, month = 1, years = -1)).strftime("%Y%m%d"))
                target_days.append((current_time + relativedelta(day = 31, month = 12, years = -1)).strftime("%Y%m%d"))
            case "一昨年":
                target_days.append((current_time + relativedelta(day = 1, month = 1, years = -2)).strftime("%Y%m%d"))
                target_days.append((current_time + relativedelta(day = 31, month = 12, years = -2)).strftime("%Y%m%d"))
            case "最後":
                target_days.append((current_time + relativedelta(days = 1)).strftime("%Y%m%d"))
            case "全部":
                target_days.append("20200101")
                target_days.append((current_time + relativedelta(days = 1)).strftime("%Y%m%d"))

            # コマンドオプションフラグ変更
            case keyword if re.search(r"^ゲスト(なし|ナシ|無し)$", keyword):
                g.opt.guest_skip = False
                g.opt.guest_skip2 = False
            case keyword if re.search(r"^ゲスト(あり|アリ)$", keyword):
                g.opt.guest_skip = True
                g.opt.guest_skip2 = True
            case keyword if re.search(r"^ゲスト無効$", keyword):
                g.opt.unregistered_replace = False
            case keyword if re.search(r"^(全員|all)$", keyword):
                g.opt.all_player = True
            case keyword if re.search(r"^(比較|点差|差分)$", keyword):
                g.opt.score_comparisons = True
            case keyword if re.search(r"^(戦績)$", keyword):
                g.opt.game_results = True
            case keyword if re.search(r"^(対戦|対戦結果)$", keyword):
                g.opt.versus_matrix = True
            case keyword if re.search(r"^(詳細|verbose)$", keyword):
                g.opt.verbose = True
            case keyword if re.search(r"^(順位)$", keyword):
                g.opt.order = True
            case keyword if re.search(r"^(統計)$", keyword):
                g.opt.statistics = True
            case keyword if re.search(r"^(個人|個人成績)$", keyword):
                g.opt.personal = True
            case keyword if re.search(r"^(直近)([0-9]+)$", keyword):
                g.opt.target_count = int(re.sub(rf"^(直近)([0-9]+)$", r"\2", keyword))
            case keyword if re.search(r"^(トップ|上位|top)([0-9]+)$", keyword):
                g.opt.ranked = int(re.sub(rf"^(トップ|上位|top)([0-9]+)$", r"\2", keyword))
            case keyword if re.search(r"^(規定数|規定打数)([0-9]+)$", keyword):
                g.opt.stipulated = int(re.sub(rf"^(規定数|規定打数)([0-9]+)$", r"\2", keyword))
            case keyword if re.search(r"^(チーム|team)$", keyword.lower()):
                g.opt.team_total = True
            case keyword if re.search(r"^(チーム同卓あり|コンビあり|同士討ち)$", keyword):
                g.opt.friendly_fire = True
            case keyword if re.search(r"^(チーム同卓なし|コンビなし)$", keyword):
                g.opt.friendly_fire = False
            case keyword if re.search(r"^(コメント|comment)(.+)$", keyword):
                g.opt.search_word = re.sub(r"^(コメント|comment)(.+)$", r"\2", keyword)
            case keyword if re.search(r"^(daily|デイリー|日次)$", keyword):
                g.opt.daily = True
            case keyword if re.search(r"^(集約)([0-9]+)$", keyword):
                g.opt.group_length = int(re.sub(rf"^(集約)([0-9]+)$", r"\2", keyword))

            # フォーマット指定
            case keyword if re.search(r"^(csv|text|txt)$", keyword.lower()):
                g.opt.format = keyword.lower()
            case keyword if re.search(r"^(filename:|ファイル名)(.+)$", keyword):
                g.opt.filename = re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword)

            # どのオプションにもマッチしないものはプレイヤー名
            case _:
                target_player.append(c.member.NameReplace(keyword))

    # 日付再取得のために再帰呼び出し
    if g.opt.recursion and not target_days:
        if "aggregation_range" in vars(g.opt):
            g.opt.recursion = False # ループ防止
            target_days, _, _, _ = argument_analysis(g.opt.aggregation_range, vars(g.opt))
            g.opt.recursion = True # 元に戻す

    # 重複排除
    target_player = list(dict.fromkeys(target_player))

    #
    g.opt.target_days = target_days
    
    return(target_days, target_player, target_count, command_option)


def len_count(text):
    """
    文字数をカウント(全角文字は2)

    Parameters
    ----------
    text : text
        判定文字列

    Returns
    -------
    count : int
        文字数
    """

    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return(count)


def HAN2ZEN(text):
    """
    半角文字を全角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(HAN, ZEN)
    return(text.translate(trans_table))


def ZEN2HAN(text):
    """
    全角文字を半角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(ZEN, HAN)
    return(text.translate(trans_table))


def HIRA2KANA(text):
    """
    ひらがなをカタカナに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(HIRA, KANA)
    return(text.translate(trans_table))


def KANA2HIRA(text):
    """
    カタカナをひらがなに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(KANA, HIRA)
    return(text.translate(trans_table))


def badge_degree(game_count = 0):
    """
    プレイしたゲーム数に対して表示される称号を返す

    Parameters
    ----------
    game_count : int
        ゲーム数

    Returns
    -------
    badge_degree : text
        表示する称号
    """

    badge_degree = ""

    if "degree" in g.config.sections():
        if g.config["degree"].getboolean("display", False):
            degree_badge = g.config.get("degree", "badge").split(",")
            degree_counter = [x for x in map(int, g.config.get("degree", "counter").split(","))]
            for i in range(len(degree_counter)):
                if game_count >= degree_counter[i]:
                    badge_degree = degree_badge[i]

    return(badge_degree)


def badge_status(game_count = 0, win = 0):
    """
    勝率に対して付く調子バッジを返す

    Parameters
    ----------
    game_count : int
        ゲーム数

    win : int
        勝ち数

    Returns
    -------
    badge_degree : text
        表示する称号
    """

    badge_status = ""

    if "status" in g.config.sections():
        if g.config["status"].getboolean("display", False):
            status_badge = g.config.get("status", "badge").split(",")
            status_step = g.config.getfloat("status", "step")
            if game_count == 0:
                index = 0
            else:
                winper = win / game_count * 100
                index = 3
                for i in (1, 2, 3):
                    if winper <= 50 - status_step * i:
                        index = 4 - i
                    if winper >= 50 + status_step * i:
                        index = 2 + i
            badge_status = status_badge[index]

    return(badge_status)


def save_output(df, format, filename):
    """
    指定されたフォーマットでdfを保存する

    Parameters
    ----------
    df : DataFrame
        保存するデータ

    format : str
        フォーマット

    filename : str
        保存ファイル名

    Returns
    -------
    save_file : file path / None
    """

    match format.lower():
        case "csv":
            data = df.to_csv(index = False)
        case "text" | "txt":
            data = df.to_markdown(index = False, tablefmt = "outline")
        case _:
            return(None)

    # 保存
    save_file = os.path.join(g.work_dir, filename)
    with open(save_file, "w") as writefile:
        writefile.writelines(data)

    return(save_file)


def set_graph_font(plt, fm):
    """
    グラフフォント設定
    """

    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()
