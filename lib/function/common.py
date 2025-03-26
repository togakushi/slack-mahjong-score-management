import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Tuple

import lib.global_value as g
from cls.parameter import CommandOption


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


def han_to_zen(text: str) -> str:
    """半角文字を全角文字に変換(数字のみ)

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(han, zen)
    return (text.translate(trans_table))


def zen_to_han(text: str) -> str:
    """全角文字を半角文字に変換(数字のみ)

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(zen, han)
    return (text.translate(trans_table))


def hira_to_kana(text: str) -> str:
    """ひらがなをカタカナに変換

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(hira, kana)
    return (text.translate(trans_table))


def kata_to_hira(text: str) -> str:
    """カタカナをひらがなに変換

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(kana, hira)
    return (text.translate(trans_table))


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


def ts_conv(ts: datetime | float, fmt: str | None = None) -> str:
    """時間フォーマット変更

    Args:
        ts (datetime | float): 変更する時間
        fmt (str | None, optional): 種類. Defaults to None.

    Returns:
        str: 変換後の文字列
    """

    time_str: Any = datetime.now()

    if isinstance(ts, float):
        time_str = datetime.fromtimestamp(ts)
    elif isinstance(ts, datetime):
        time_str = ts

    match fmt:
        case "ts":
            ret = str(time_str.timestamp())
        case "yyyymmdd":
            ret = time_str.strftime("%Y/%m/%d")
        case "yyyymmdd_hhmm":
            ret = time_str.strftime("%Y/%m/%d %H:%M")
        case _:
            ret = time_str.strftime("%Y/%m/%d %H:%M:%S")

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
    check_list += [kata_to_hira(i) for i in g.member_list]  # ひらがな
    check_list += [hira_to_kana(i) for i in g.member_list]  # カタカナ
    if name in check_list:
        return (False, f"「{name}」は存在するメンバーです。")

    # 登録済みチームかチェック
    for x in [x["team"] for x in g.team_list]:
        if name == x:
            return (False, f"「{name}」は存在するチームです。")
        if kata_to_hira(name) == kata_to_hira(x):  # ひらがな
            return (False, f"「{name}」は存在するチームです。")
        if hira_to_kana(name) == hira_to_kana(x):  # カタカナ
            return (False, f"「{name}」は存在するチームです。")

    # 登録規定チェック
    if kind is not None and g.cfg.config.has_section(kind):
        if len(name) > g.cfg.config[kind].getint("character_limit", 8):  # 文字制限
            return (False, "登録可能文字数を超えています。")
    if name in [g.prm.guest_name, "nan"]:  # 登録NGプレイヤー名
        return (False, "使用できない名前です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        return (False, "使用できない記号が含まれています。")

    # コマンドと同じ名前かチェック
    if g.search_word.find(name):
        return (False, "検索範囲指定に使用される単語では登録できません。")

    chk = CommandOption()
    chk.check([name])
    if vars(chk):
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

    badge_degree = ""

    if "degree" in g.cfg.config.sections():
        if g.cfg.config["degree"].getboolean("display", False):
            degree_badge = g.cfg.config.get("degree", "badge").split(",")
            degree_counter = list(map(int, g.cfg.config.get("degree", "counter").split(",")))
            for idx, val in enumerate(degree_counter):
                if game_count >= val:
                    badge_degree = degree_badge[idx]

    return (badge_degree)


def badge_status(game_count: int = 0, win: int = 0) -> str:
    """勝率に対して付く調子バッジを返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.
        win (int, optional): 勝ち数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge_status = ""

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
            badge_status = status_badge[index]

    return (badge_status)


def floatfmt_adjust(df, index=False) -> list:
    """カラム名に応じたfloatfmtのリストを返す

    Args:
        index (bool): リストにIndexを含める
        df (pd.DataFrame): チェックするデータ

    Returns:
        list: floatfmtに指定するリスト
    """

    fmt: list = []
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


def save_output(df, kind: str, filename: str, headline: str | None = None) -> str | None:
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
            data = df.to_markdown(index=False, tablefmt="outline", floatfmt=floatfmt_adjust(df))
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


def scope_coverage(argument: list) -> Tuple[list, list]:
    """キーワードから有効な日付を取得する

    Args:
        argument (list): 引数リスト

    Returns:
        Tuple[list,list]:
            - list: 得られた日付のリスト
            - list: 日付を取り除いた引数リスト
    """

    new_argument = argument.copy()
    target_days = []

    for x in argument:
        if g.search_word.find(x):
            target_days += g.search_word.range(x)
            new_argument.remove(x)

    return (target_days, new_argument)


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
