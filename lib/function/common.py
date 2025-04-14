"""
lib/function/common.py
"""

import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Tuple, Literal

import pandas as pd

import lib.global_value as g


def len_count(text: str) -> int:
    """文字数をカウント(全角文字は2)

    Args:
        text (str): 判定文字列

    Returns:
        int: 文字数
    """

    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return (count)


def merge_dicts(dict1: Any, dict2: Any) -> dict:
    """辞書の内容をマージする

    Args:
        dict1 (Any): 1つ目の辞書
        dict2 (Any): 2つ目の辞書

    Returns:
        dict: マージされた辞書
    """

    merged: dict = {}

    for key in set(dict1) | set(dict2):
        val1: Any = dict1.get(key)
        val2: Any = dict2.get(key)

        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            merged[key] = val1 + val2
        elif isinstance(val1, str) and isinstance(val2, str):
            merged[key] = val1 + val2
        elif isinstance(val1, list) and isinstance(val2, list):
            merged[key] = sorted(list(set(val1 + val2)))
        else:
            merged[key] = val1 if val2 is None else val2

    return (merged)


def str_conv(text: str, kind: Literal["h2z", "z2h", "h2k", "k2h"]) -> str:
    """文字列変換

    Args:
        text (str): 変換対象文字列
        kind (str): 変換種類
            - h2z: 半角文字を全角文字に変換(数字のみ)
            - z2h: 全角文字を半角文字に変換(数字のみ)
            - h2k: ひらがなをカタカナに変換
            - k2h: カタカナをひらがなに変換

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))

    match kind:
        case "h2z":  # 半角文字を全角文字に変換(数字のみ)
            trans_table = str.maketrans(han, zen)
        case "z2h":  # 全角文字を半角文字に変換(数字のみ)
            trans_table = str.maketrans(zen, han)
        case "h2k":  # ひらがなをカタカナに変換
            trans_table = str.maketrans(hira, kana)
        case "k2h":  # カタカナをひらがなに変換
            trans_table = str.maketrans(kana, hira)
        case _:
            return (text)

    return (text.translate(trans_table))


def ts_conv(ts: datetime | float | str, fmt: Literal["ts", "y", "jy", "m", "jm", "d", "hm", "hms"] | str) -> str:
    """時間書式変更

    Args:
        ts (datetime | float | str): 変更する時間
        fmt (str | None, optional): フォーマット指定. Defaults to None.
            - ts: timestamp()
            - y / jy: "%Y" / "%Y年"
            - m / jm: "%Y/%m" / "%Y年%m月"
            - d: "%Y/%m/%d"
            - hm: "%Y/%m/%d %H:%M"
            - hms: "%Y/%m/%d %H:%M:%S"

    Returns:
        str: 変更後の文字列
    """

    time_obj: Any = datetime.now()

    if isinstance(ts, str):
        time_obj = datetime.fromisoformat(ts)
    elif isinstance(ts, float):
        time_obj = datetime.fromtimestamp(ts)
    elif isinstance(ts, datetime):
        time_obj = ts

    match fmt:
        case "ts":
            ret = str(time_obj.timestamp())
        case "y":
            ret = time_obj.strftime("%Y")
        case "jy":
            ret = time_obj.strftime("%Y年")
        case "jm":
            ret = time_obj.strftime("%Y年%m月")
        case "d":
            ret = time_obj.strftime("%Y/%m/%d")
        case "hm":
            ret = time_obj.strftime("%Y/%m/%d %H:%M")
        case "hms":
            ret = time_obj.strftime("%Y/%m/%d %H:%M:%S")

    return (ret)


def check_namepattern(name: str, kind: str | None = None) -> Tuple[bool, str]:
    """登録制限チェック

    Args:
        name (str): チェックする名前
        kind (str | None, optional): チェック種別. Defaults to None.

    Returns:
        Tuple[bool,str]: 判定結果
            - bool: 制限チェック結果真偽
            - str: 制限理由
    """

    # 登録済みメンバーかチェック
    check_list = list(g.member_list.keys())
    check_list += [str_conv(i, "k2h") for i in g.member_list]  # ひらがな
    check_list += [str_conv(i, "h2k") for i in g.member_list]  # カタカナ
    if name in check_list:
        return (False, f"「{name}」は存在するメンバーです。")

    # 登録済みチームかチェック
    for x in [x["team"] for x in g.team_list]:
        if name == x:
            return (False, f"「{name}」は存在するチームです。")
        if str_conv(name, "k2h") == str_conv(x, "k2h"):  # ひらがな
            return (False, f"「{name}」は存在するチームです。")
        if str_conv(name, "h2k") == str_conv(x, "h2k"):  # カタカナ
            return (False, f"「{name}」は存在するチームです。")

    # 登録規定チェック
    if kind is not None and g.cfg.config.has_section(kind):
        if len(name) > g.cfg.config[kind].getint("character_limit", 8):  # 文字制限
            return (False, "登録可能文字数を超えています。")
    if name in [g.cfg.member.guest_name, "nan"]:  # 登録NGプレイヤー名
        return (False, "使用できない名前です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        return (False, "使用できない記号が含まれています。")

    # 引数に利用できる名前かチェック
    if g.search_word.find(name):
        return (False, "検索範囲指定に使用される単語では登録できません。")

    check = analysis_argument([name, f"{name}999"])
    check.pop("search_range")
    check.pop("unknown_command")
    if check:
        return (False, "オプションに使用される単語では登録できません。")

    if name in g.cfg.word_list():
        return (False, "コマンドに使用される単語では登録できません。")

    return (True, "OK")


def badge_degree(game_count: int = 0) -> str:
    """プレイしたゲーム数に対して表示される称号を返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if "degree" in g.cfg.config.sections():
        if g.cfg.config["degree"].getboolean("display", False):
            degree_badge = g.cfg.config.get("degree", "badge").split(",")
            degree_counter = list(map(int, g.cfg.config.get("degree", "counter").split(",")))
            for idx, val in enumerate(degree_counter):
                if game_count >= val:
                    badge = degree_badge[idx]

    return (badge)


def badge_status(game_count: int = 0, win: int = 0) -> str:
    """勝率に対して付く調子バッジを返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.
        win (int, optional): 勝ち数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if "status" in g.cfg.config.sections():
        if g.cfg.config["status"].getboolean("display", False):
            status_badge = g.cfg.config.get("status", "badge").split(",")
            status_step = g.cfg.config.getfloat("status", "step")
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
            badge = status_badge[index]

    return (badge)


def floatfmt_adjust(df: pd.DataFrame, index: bool = False) -> list:
    """カラム名に応じたfloatfmtのリストを返す

    Args:
        df (pd.DataFrame): チェックするデータ
        index (bool, optional): リストにIndexを含める. Defaults to False.

    Returns:
        list: floatfmtに指定するリスト
    """

    fmt: list = []
    if df.empty:
        return (fmt)

    field: list = df.columns.tolist()
    if index:
        field.insert(0, df.index.name)

    for x in field:
        match x:
            case "ゲーム数" | "game_count":
                fmt.append(".0f")
            case "win" | "lose" | "draw" | "top2" | "top3" | "gs_count":
                fmt.append(".0f")
            case "通算" | "通算ポイント" | "point_sum":
                fmt.append("+.1f")
            case "平均" | "平均ポイント" | "point_avg" | "区間ポイント" | "区間平均":
                fmt.append("+.1f")
            case "1st" | "2nd" | "3rd" | "4th" | "1位" | "2位" | "3位" | "4位" | "rank1" | "rank2" | "rank3" | "rank4":
                fmt.append(".0f")
            case "1st(%)" | "2nd(%)" | "3rd(%)" | "4th(%)" | "1位率" | "2位率" | "3位率" | "4位率":
                fmt.append(".2f")
            case "トビ" | "flying":
                fmt.append(".0f")
            case "トビ率":
                fmt.append(".2f")
            case "平均順位" | "平順" | "rank_avg":
                fmt.append(".2f")
            case "順位差" | "トップ差":
                fmt.append(".1f")
            case "レート":
                fmt.append(".1f")
            case "順位偏差" | "得点偏差":
                fmt.append(".0f")
            case "rpoint_max" | "rpoint_min" | "rpoint_mean":
                fmt.append(".0f")
            case _:
                fmt.append("")

    return (fmt)


def column_alignment(df: pd.DataFrame, header: bool = False, index: bool = False) -> list:
    """カラム位置

    Args:
        df (pd.DataFrame): チェックするデータ
        header (bool, optional): ヘッダを対象にする
        index (bool, optional): リストにIndexを含める. Defaults to False.

    Returns:
        list: colalignに指定するリスト
    """

    fmt: list = []  # global, right, center, left, decimal, None
    if df.empty:
        return (fmt)

    field: list = df.columns.tolist()
    if index:
        field.insert(0, df.index.name)

    if header:  # ヘッダ(すべて左寄せ)
        fmt = ["left"] * len(field)
    else:
        for x in field:
            match x:
                case "ゲーム数":
                    fmt.append("right")
                case "通算" | "平均" | "1位" | "2位" | "3位" | "4位" | " 平順" | "トビ":
                    fmt.append("right")
                case "通算" | "順位差" | "トップ差":
                    fmt.append("right")
                case "レート" | "平均順位" | "順位偏差" | "平均素点" | "得点偏差":
                    fmt.append("right")
                case _:
                    fmt.append("left")

    return (fmt)


def save_output(df: pd.DataFrame, kind: str, filename: str, headline: str | None = None) -> str | None:
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): _description_
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (str | None, optional): 集計情報（ヘッダコメント）. Defaults to None.

    Returns:
        Union[str, None]
            - str: 保存したファイルパス
            - None: 指定したフォーマットで保存できなかった場合
    """

    match kind.lower():
        case "csv":
            data = df.to_csv(index=False)
        case "text" | "txt":
            data = df.to_markdown(
                index=False,
                tablefmt="outline",
                floatfmt=floatfmt_adjust(df),
                colalign=column_alignment(df, False),
                # headersalign=column_alignment(df, True),  # ToDo: python-tabulate >= 0.10.0
            )
        case _:
            return (None)

    # 保存
    save_file = os.path.join(g.cfg.setting.work_dir, filename)
    with open(save_file, "w", encoding="utf-8") as writefile:
        if headline is not None:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return (save_file)


def graph_setup(plt, fm) -> None:
    """グラフ設定

    Args:
        plt (matplotlib.font_manager): matplotlibオブジェクト
        fm (matplotlib.pyplot): matplotlibオブジェクト
    """

    # スタイルの適応
    style = g.cfg.config["setting"].get("graph_style", "ggplot")

    if style not in plt.style.available:
        style = "ggplot"

    plt.style.use(style)

    # フォント再設定
    for x in ("family", "serif", "sans-serif", "cursive", "fantasy", "monospace"):
        if f"font.{x}" in plt.rcParams:
            plt.rcParams[f"font.{x}"] = ""

    font_path = os.path.join(os.path.realpath(os.path.curdir), g.cfg.setting.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    # グリッド線
    if not plt.rcParams["axes.grid"]:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.alpha"] = 0.3
        plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["axes.axisbelow"] = True


def analysis_argument(argument: list) -> dict:
    """引数解析

    Args:
        argument (list): 引数

    Returns:
        dict: 更新フラグ/パラメータ
    """

    ret: dict = {}

    # コマンドオプションフラグ変更
    unknown_command: list = []
    search_range: list = []

    if g.cfg.comment.search_word:
        ret.update(search_word=g.cfg.comment.search_word)
        ret.update(group_length=g.cfg.comment.group_length)

    for keyword in argument:
        check_word = str_conv(keyword.lower(), "h2k")  # カタカナ、小文字に統一
        check_word = check_word.replace("無シ", "ナシ").replace("有リ", "アリ")  # 表記統一

        if g.search_word.find(keyword):
            search_range.append(keyword)
            continue

        if re.match(r"^([0-9]{8}|[0-9/.-]{8,10})$", keyword):
            search_range.append(keyword)
            continue

        match check_word:
            case check_word if re.search(r"^ゲストナシ$", check_word):
                ret.update(guest_skip=False)
                ret.update(guest_skip2=False)
                ret.update(unregistered_replace=True)
            case check_word if re.search(r"^ゲストアリ$", check_word):
                ret.update(guest_skip=True)
                ret.update(guest_skip2=True)
                ret.update(unregistered_replace=True)
            case check_word if re.search(r"^ゲスト無効$", check_word):
                ret.update(unregistered_replace=False)
            case check_word if re.search(r"^(全員|all)$", check_word):
                ret.update(all_player=True)
            case check_word if re.search(r"^(比較|点差|差分)$", check_word):
                ret.update(score_comparisons=True)
            case check_word if re.search(r"^(戦績)$", check_word):
                ret.update(game_results=True)
            case check_word if re.search(r"^(対戦|対戦結果)$", check_word):
                ret.update(versus_matrix=True)
            case check_word if re.search(r"^(詳細|verbose)$", check_word):
                ret.update(verbose=True)
            case check_word if re.search(r"^(順位)$", check_word):
                ret.update(order=True)
            case check_word if re.search(r"^(統計)$", check_word):
                ret.update(statistics=True)
            case check_word if re.search(r"^(レート|レーティング|rate|ratings?)$", check_word):
                ret.update(rating=True)
            case check_word if re.search(r"^(個人|個人成績)$", check_word):
                ret.update(individual=True)
            case check_word if re.search(r"^(チーム|チーム成績|team)$", check_word):
                ret.update(individual=False)
            case check_word if re.search(r"^(直近)([0-9]+)$", check_word):
                ret.update(target_count=int(re.sub(r"^(直近)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(トップ|上位|top)([0-9]+)$", check_word):
                ret.update(ranked=int(re.sub(r"^(トップ|上位|top)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(規定数|規定打数)([0-9]+)$", check_word):
                ret.update(stipulated=int(re.sub(r"^(規定数|規定打数)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(区間|区切リ?|interval)([0-9]+)$", check_word):
                ret.update(interval=int(re.sub(r"^(区間|区切リ?|interval)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(チーム同卓アリ|コンビアリ|同士討チ)$", check_word):
                ret.update(friendly_fire=True)
            case check_word if re.search(r"^(チーム同卓ナシ|コンビナシ)$", check_word):
                ret.update(friendly_fire=False)
            case check_word if re.search(r"^(コメント|comment)(.+)$", check_word):
                ret.update(search_word=re.sub(r"^(コメント|comment)(.+)$", r"\2", check_word))
            case check_word if re.search(r"^(daily|デイリー|日次)$", check_word):
                ret.update(collection="daily")
            case check_word if re.search(r"^(monthly|マンスリー|月次)$", check_word):
                ret.update(collection="monthly")
            case check_word if re.search(r"^(yearly|イヤーリー|年次)$", check_word):
                ret.update(collection="yearly")
            case check_word if re.search(r"^(全体)$", check_word):
                ret.update(collection="all")
            case check_word if re.search(r"^(集約)([0-9]+)$", check_word):
                ret.update(group_length=int(re.sub(r"^(集約)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(ルール|rule)(.+)$", check_word):
                ret.update(rule_version=re.sub(r"^(ルール|rule)(.+)$", r"\2", keyword))
            case check_word if re.search(r"^(csv|text|txt)$", check_word):
                ret.update(format=check_word)
            case check_word if re.search(r"^(filename:|ファイル名)(.+)$", check_word):
                ret.update(filename=re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword))
            case check_word if re.search(r"^(匿名|anonymous)$", check_word):
                ret.update(anonymous=True)
            case _:
                unknown_command.append(keyword)

    ret.update(search_range=search_range)
    ret.update(unknown_command=unknown_command)
    return (ret)


def debug_out(msg1: str, msg2: str | dict | list | bool | None = None) -> None:
    """メッセージ標準出力(テスト用)

    Args:
        msg1 (str): _description_
        msg2 (str | dict | list | bool | None, optional): _description_. Defaults to None.
    """

    print(msg1)
    if isinstance(msg2, dict):
        for _, val in msg2.items():
            print(val)
    elif msg2:
        print(msg2)
