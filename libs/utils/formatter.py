"""
libs/utils/formatter.py
"""

import os
import random
import re

import pandas as pd

import libs.global_value as g
from libs.data import lookup
from libs.utils import textutil


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
        return fmt

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

    return fmt


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
        return fmt

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

    return fmt


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
            return None

    # 保存
    save_file = os.path.join(g.cfg.setting.work_dir, filename)
    with open(save_file, "w", encoding="utf-8") as writefile:
        if headline is not None:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return save_file


def debug_out(msg1: str | list, msg2: str | dict | list | bool | None = None) -> None:
    """メッセージ標準出力(テスト用)

    Args:
        msg1 (str | list): メッセージ1
        msg2 (str | dict | list | bool | None, optional): メッセージ2. Defaults to None.
    """

    print(msg1)
    if isinstance(msg2, dict):
        for _, val in msg2.items():
            print(val)
    elif msg2:
        print(msg2)


def name_replace(pname: str, add_mark: bool = False) -> str:
    """表記ブレ修正(正規化)

    Args:
        pname (str): 対象プレイヤー名
        add_mark (bool, optional): ゲストマークを付与する. Defaults to False.

    Returns:
        str: 表記ブレ修正後のプレイヤー名
    """

    check_list = list(set(g.member_list.keys()))  # 別名を含むリスト
    check_team = lookup.internal.get_team()

    def _judge(check: str) -> str:
        if g.params.get("individual"):
            if check in check_list:
                return g.member_list.get(check, check)
        else:
            if check in check_team:
                return check
        return ""

    if (ret_name := _judge(textutil.str_conv(pname, "h2z"))):  # 半角数字 -> 全角数字
        return ret_name

    pname = honor_remove(pname)  # 敬称削除

    if (ret_name := _judge(pname)):
        return ret_name

    if (ret_name := _judge(textutil.str_conv(pname, "k2h"))):  # カタカナ -> ひらがな
        return ret_name

    if (ret_name := _judge(textutil.str_conv(pname, "h2k"))):  # ひらがな -> カタカナ
        return ret_name

    # メンバーリストに見つからない場合
    if g.params.get("unregistered_replace"):
        pname = g.cfg.member.guest_name
    elif add_mark:
        pname = f"{pname}({g.cfg.setting.guest_mark})"

    return pname


def honor_remove(name: str) -> str:
    """敬称削除

    Args:
        name (str): 対象の名前

    Returns:
        str: 敬称を削除した名前
    """

    honor = r"(くん|さん|ちゃん|クン|サン|チャン|君)$"
    if re.match(fr".*{honor}", name):
        if not re.match(fr".*(っ|ッ|ー){honor}", name):
            name = re.sub(fr"{honor}", "", name)

    return name


def anonymous_mapping(name_list: list, initial: int = 0) -> dict:
    """名前リストから変換用辞書を生成

    Args:
        name_list (list): 名前リスト
        initial (int, optional): インデックス初期値. Defaults to 0.

    Returns:
        dict: マッピング用辞書
    """

    ret: dict = {}

    if g.params.get("individual", True):
        prefix = "Player"
        id_list = lookup.db.get_member_id()
    else:
        prefix = "Team"
        id_list = {x["team"]: x["id"] for x in g.team_list}

    if len(name_list) == 1:
        name = name_list[0]
        if name in id_list:
            idx = id_list[name]
        else:
            idx = int(random.random() * 100 + 100)
        ret[name] = f"{prefix}_{idx + initial:03d}"
    else:
        random.shuffle(name_list)
        for idx, name in enumerate(name_list):
            ret[name] = f"{prefix}_{idx + initial:03d}"

    return ret


def df_rename(df: pd.DataFrame, short=True) -> pd.DataFrame:
    """カラム名をリネームする

    Args:
        df (pd.DataFrame): 対象データフレーム
        short (bool, optional): 略語にリネーム. Defaults to True.

    Returns:
        pd.DataFrame: リネーム後のデータフレーム
    """

    rename_dict: dict = {
        "playtime": "日時",
        "rate": "レート",
        #
        "rpoint": "素点",
        "point": "獲得ポイント",
        "rpoint_avg": "平均素点",
        "point_dev": "得点偏差", "rank_dev": "順位偏差",
        "grade": "段位",
        # レコード
        "max_top": "連続トップ", "max_top2": "連続連対", "max_top3": "連続ラス回避",
        "max_low": "連続トップなし", "max_low2": "連続逆連対", "max_low4": "連続ラス",
        "max_point": "最大獲得ポイント", "min_point": "最小獲得ポイント",
        "max_rpoint": "最大素点", "min_rpoint": "最小素点",
        # 直接対決
        "results": "対戦結果", "win%": "勝率",
        "my_point_sum": "獲得ポイント(自分)", "my_point_avg": "平均ポイント(自分)",
        "vs_point_sum": "獲得ポイント(相手)", "vs_point_avg": "平均ポイント(相手)",
        "my_rpoint_avg": "平均素点(自分)", "my_rank_avg": "平均順位(自分)", "my_rank_distr": "順位分布(自分)",
        "vs_rpoint_avg": "平均素点(相手)", "vs_rank_avg": "平均順位(相手)", "vs_rank_distr": "順位分布(相手)",
    }

    for x in df.columns:
        match x:
            case "rank":
                rename_dict[x] = "#" if short else "順位"
            case "name" | "player":
                rename_dict[x] = "名前" if short else "プレイヤー名"
            case "team":
                rename_dict[x] = "チーム" if short else "チーム名"
            case "count" | "game":
                rename_dict[x] = "ゲーム数"
            case "pt_total" | "total_point" | "point_sum" | "total_mix":
                rename_dict[x] = "通算" if short else "通算ポイント"
            case "pt_avg" | "avg_point" | "point_avg" | "avg_mix":
                rename_dict[x] = "平均" if short else "平均ポイント"
            case "ex_point":
                rename_dict[x] = "卓外" if short else "卓外ポイント"
            case "rank_distr" | "rank_distr1" | "rank_distr2":
                rename_dict[x] = "順位分布"
            case "rank_avg":
                rename_dict[x] = "平順" if short else "平均順位"
            case "1st" | "rank1" | "1st_mix":
                rename_dict[x] = "1位"
            case "2nd" | "rank2" | "2nd_mix":
                rename_dict[x] = "2位"
            case "3rd" | "rank3" | "3rd_mix":
                rename_dict[x] = "3位"
            case "4th" | "rank4" | "4th_mix":
                rename_dict[x] = "4位"
            case "1st(%)" | "1st_%" | "rank1_rate":
                rename_dict[x] = "1位率"
            case "2nd(%)" | "2nd_%" | "rank2_rate":
                rename_dict[x] = "2位率"
            case "3rd(%)" | "3rd_%" | "rank3_rate":
                rename_dict[x] = "3位率"
            case "4th(%)" | "4th_%" | "rank4_rate":
                rename_dict[x] = "4位率"
            case "1st_count":
                rename_dict[x] = "1位数"
            case "2nd_count":
                rename_dict[x] = "2位数"
            case "3rd_count":
                rename_dict[x] = "3位数"
            case "4th_count":
                rename_dict[x] = "4位数"
            case "flying" | "flying_mix":
                rename_dict[x] = "トビ"
            case "flying_count":
                rename_dict[x] = "トビ数"
            case "flying_rate" | "flying_%":
                rename_dict[x] = "トビ率"
            case "pt_diff":
                rename_dict[x] = "差分"
            case "diff_from_above":
                rename_dict[x] = "順位差"
            case "diff_from_top":
                rename_dict[x] = "トップ差"
            case "yakuman_mix" | "grandslam":
                rename_dict[x] = "役満和了"
            case "yakuman_count":
                rename_dict[x] = "役満和了数"
            case "yakuman_%":
                rename_dict[x] = "役満和了率"

    if not g.params.get("individual"):
        rename_dict.update(name="チーム" if short else "チーム名")

    return df.rename(columns=rename_dict)
