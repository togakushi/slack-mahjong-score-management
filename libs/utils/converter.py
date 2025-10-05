"""
libs/utils/converter.py
"""


import os
import re
import textwrap
from typing import Optional, cast

import pandas as pd
from tabulate import tabulate

import libs.global_value as g
from libs.utils import formatter, textutil


def save_output(
    df: pd.DataFrame,
    kind: str,
    filename: str,
    headline: Optional[str] = None,
) -> str:
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): 描写対象データ
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (Optional[str], optional): 集計情報（ヘッダコメント）. Defaults to None.

    Returns:
        str: 保存したファイルパス
    """

    match kind.lower():
        case "csv":
            data = df.to_csv(index=False)
        case "text" | "txt":
            data = df.to_markdown(
                index=False,
                tablefmt="outline",
                floatfmt=formatter.floatfmt_adjust(df),
                colalign=formatter.column_alignment(df, False),
                # headersalign=column_alignment(df, True),  # ToDo: python-tabulate >= 0.10.0
            )
        case _:
            return ""

    # 保存
    save_file = os.path.join(g.cfg.setting.work_dir, filename)
    with open(save_file, "w", encoding="utf-8") as writefile:
        if headline is not None:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return save_file


def df_to_dict(df: pd.DataFrame, step: int = 40, index: bool = False) -> dict:
    """DataFrameからテキスト変換

    Args:
        df (pd.DataFrame): 対象データ
        step (int, optional): 分割行. Defaults to 40.
        index (bool, optional): インデックスを含める. Defaults to False.

    Returns:
        dict: 整形テキスト
    """

    msg: dict = {}
    floatfmt = formatter.floatfmt_adjust(df, index)

    # インデックスの振りなおし
    df.reset_index(inplace=True, drop=True)
    df.index += 1

    def _to_text(tmp_df: pd.DataFrame) -> str:
        ret = tmp_df.to_markdown(
            index=index,
            tablefmt="simple",
            numalign="right",
            floatfmt=floatfmt,
        ).replace("   nan", "******")
        ret = re.sub(r"  -([0-9]+)", r" ▲\1", ret)  # マイナスを記号に置換
        return ret

    if step:
        for s_line, e_line in textutil.split_line(len(df), step):
            t = _to_text(df[s_line:e_line])
            msg[str(s_line)] = t
    else:
        t = _to_text(df)
        msg["0"] = t

    return msg


def df_to_results_details(df: pd.DataFrame) -> dict:
    """戦績(詳細)データをテキスト変換

    Args:
        df (pd.DataFrame): 対象データ

    Returns:
        dict: 整形テキスト
    """

    data_list: list = []
    for x in df.to_dict(orient="index").values():
        work_df = pd.DataFrame({
            "東家：": [v for k, v in cast(dict, x).items() if str(k).startswith("東家")],
            "南家：": [v for k, v in cast(dict, x).items() if str(k).startswith("南家")],
            "西家：": [v for k, v in cast(dict, x).items() if str(k).startswith("西家")],
            "北家：": [v for k, v in cast(dict, x).items() if str(k).startswith("北家")],
        }, index=["name", "rpoint", "rank", "point", "grandslam"]).T

        work_df["rpoint"] = work_df.apply(lambda v: f"<>{v["rpoint"]:8d}点".replace("-", "▲"), axis=1)
        work_df["point"] = work_df.apply(lambda v: f"(<>{v["point"]:7.1f}pt)".replace("-", "▲"), axis=1)
        work_df["rank"] = work_df.apply(lambda v: f"{v["rank"]}位", axis=1)
        data = work_df.to_markdown(tablefmt="tsv", headers=[], floatfmt=formatter.floatfmt_adjust(work_df)).replace("<>", "")

        ret = f"{str(x["日時"]).replace("-", "/")} {x["備考"]}\n"
        ret += textwrap.indent(data, "\t") + "\n"

        data_list.append(ret)

    return {str(idx): x for idx, x in enumerate(formatter.group_strings(data_list, 2000))}


def df_to_results_simple(df: pd.DataFrame) -> dict:
    """戦績(簡易)データをテキスト変換

    Args:
        df (pd.DataFrame): 対象データ

    Returns:
        dict: 整形テキスト
    """

    data_list: list = []
    for x in df.to_dict(orient="index").values():
        vs_guest = ""
        if x["備考"] != "":
            vs_guest = f"({g.cfg.setting.guest_mark}) "

        ret = f"\t{vs_guest}{str(x["日時"]).replace("-", "/")}  "
        ret += f"{x["座席"]}\t{x["順位"]}位\t{x["素点"]:8d}点\t({x["ポイント"]:7.1f}pt)\t{x["役満和了"]}".replace("-", "▲")
        data_list.append(ret)

    return {str(idx): x for idx, x in enumerate(formatter.group_strings(data_list, 2500))}


def df_to_ranking(df: pd.DataFrame, title: str, step: int = 40) -> dict:
    """DataFrameからランキングテーブルを生成

    Args:
        df (pd.DataFrame): 対象データ
        title (str): 種別
        step (int, optional): 分割行. Defaults to 40.

    Returns:
        dict: 整形テキスト
    """

    # 表示内容
    match title:
        case "ゲーム参加率":
            df["内容"] = df.apply(lambda x: f"<>{x["ゲーム参加率"]:>7.2%} ({x["ゲーム数"]:4d}G /{x["集計ゲーム数"]:4d}G)", axis=1)
        case "通算ポイント":
            df["内容"] = df.apply(lambda x: f"<>{x["通算ポイント"]:>+8.1f}pt ({x["ゲーム数"]:4d}G)", axis=1)
        case "平均ポイント":
            df["内容"] = df.apply(lambda x: f"<>{x["平均ポイント"]:>+8.1f}pt ( {x["通算ポイント"]:>+8.1f}pt /{x["ゲーム数"]:4d}G)", axis=1)
        case "平均収支":
            df["内容"] = df.apply(lambda x: f"<>{x["平均収支"]:>6.0f}点 ({x["平均素点"]:>6.0f}点 /{x["ゲーム数"]:4d}G)", axis=1)
        case "トップ率":
            df["内容"] = df.apply(lambda x: f"<>{x["1位率"]:>7.2%} ({x["1位数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "連対率":
            df["内容"] = df.apply(lambda x: f"<>{x["連対率"]:>7.2%} ({x["連対数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "ラス回避率":
            df["内容"] = df.apply(lambda x: f"<>{x["ラス回避率"]:>7.2%} ({x["ラス回避数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "トビ率":
            df["内容"] = df.apply(lambda x: f"<>{x["トビ率"]:>7.2%} ({x["トビ数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "平均順位":
            df["内容"] = df.apply(lambda x: f"<>{x["平均順位"]:>4.2f} ({x["順位分布"]})", axis=1)
        case "役満和了率":
            df["内容"] = df.apply(lambda x: f"<>{x["役満和了率"]:>7.2%} ({x["役満和了数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "最大素点":
            df["内容"] = df.apply(lambda x: f"<>{x["最大素点"]:>6.0f}点 ({x["最大獲得ポイント"]:>+8.1f}pt)", axis=1)
        case "連続トップ":
            df["内容"] = df.apply(lambda x: f"<>{x["連続トップ"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case "連続連対":
            df["内容"] = df.apply(lambda x: f"<>{x["連続連対"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case "連続ラス回避":
            df["内容"] = df.apply(lambda x: f"<>{x["連続ラス回避"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case _:
            return {}

    # 整形と分割
    ret_list: list = []
    for s_line, e_line in textutil.split_line(len(df), step):
        work_df = df[s_line:e_line]
        tbl = tabulate(work_df.filter(items=["順位", "プレイヤー名", "内容"]).values, showindex=False)
        ret = ""
        for line in tbl.splitlines()[1:-1]:
            line = re.sub(r"^(\s*\d+)(.*)", r"\1：\2", line)
            line = line.replace(" -", "▲")
            line = line.replace("<>", "")
            ret += f"{line}\n"
        ret_list.append(ret.rstrip())

    return {str(idx): data for idx, data in enumerate(ret_list)}


def df_to_remarks(df: pd.DataFrame) -> dict:
    """DataFrameからメモテーブルを生成

    Args:
        df (pd.DataFrame): 対象データ

    Returns:
        dict: 整形テキスト
    """

    for col in df.columns:
        match col:
            case "日時":
                df["日時"] = df["日時"].map(lambda x: str(x).replace("-", "/"))
            case "卓外":
                df["卓外"] = df["卓外"].map(lambda x: f"{x}pt".replace("-", "▲"))

    if "卓外" in df.columns:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["内容"]} {x["卓外"]} ({x["名前"]})", axis=1)
    elif "和了役" in df.columns:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["和了役"]} ({x["名前"]})", axis=1)
    else:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["内容"]} ({x["名前"]})", axis=1)

    tbl = tabulate(df.filter(items=["表示"]).values, showindex=False).splitlines()[1:-1]

    return {"0": "\n".join(tbl)}


def df_to_count(df: pd.DataFrame, title: str, indent: int = 0) -> dict:
    """DataFrameからメモの回数表示を生成

    Args:
        df (pd.DataFrame): 対象データ
        title (str): _description_
        indent (int, optional): インデント. Defaults to 0.

    Returns:
        dict: 整形テキスト
    """
    match title:
        case "役満和了":
            df["表示"] = df.apply(lambda x: f"{x["和了役"]}： {x["回数"]} 回", axis=1)
        case "卓外ポイント":
            df["表示"] = df.apply(lambda x: f"{x["内容"]}： {x["回数"]} 回 ({x["ポイント合計"]:.1f}pt)".replace("-", "▲"), axis=1)
        case "その他":
            df["表示"] = df.apply(lambda x: f"{x["内容"]}： {x["回数"]} 回", axis=1)

    tbl = tabulate(df.filter(items=["表示"]).values, showindex=False).splitlines()[1:-1]
    return {"0": textwrap.indent("\n".join(tbl), "\t" * indent)}


def df_to_seat_data(df: pd.DataFrame, indent: int = 0) -> dict:
    """座席データ生成

    Args:
        df (pd.DataFrame): 対象データ
        indent (int, optional): インデント. Defaults to 0.

    Returns:
        dict: 整形テキスト
    """

    # 表示加工
    df["順位分布(平均順位)"] = df.apply(lambda x: f"{x["順位分布"]} ({x["平均順位"]:.2f})", axis=1)
    df.drop(columns=["順位分布", "平均順位"], inplace=True)
    df["席"] = df.apply(lambda x: f"{x["席"]}：", axis=1)
    if "トビ" in df.columns:
        df["トビ"] = df.apply(lambda x: f"/ {x["トビ"]:3d}", axis=1)
    if "役満和了" in df.columns:
        df["役満和了"] = df.apply(lambda x: f"/ {x["役満和了"]:3d}", axis=1)

    #
    df = df.filter(items=["席", "順位分布(平均順位)", "トビ", "役満和了"]).rename(
        columns={
            "席": "# 席：",
            "トビ": "/ トビ",
            "役満和了": "/ 役満 #"
        }
    )

    tbl = df.to_markdown(tablefmt="tsv", index=False).replace("0.00", "-.--").replace(" \t", "")
    return {"0": textwrap.indent(tbl, "\t" * indent)}
