"""
libs/utils/converter.py
"""


import os
import re
import textwrap

import pandas as pd
from tabulate import tabulate

import libs.global_value as g
from libs.utils import formatter, textutil


def save_output(df: pd.DataFrame, kind: str, filename: str, headline: str | None = None) -> str:
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): 描写対象データ
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (str | None, optional): 集計情報（ヘッダコメント）. Defaults to None.

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


def df_to_ranking(df: pd.DataFrame, title: str, step: int = 40) -> dict:
    """DataFrameからランキングテーブルを生成

    Args:
        df (pd.DataFrame): ランキングデータ
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
            df["内容"] = df.apply(lambda x: f"<>{x["通算ポイント"]:>+7.1f}pt ({x["ゲーム数"]:4d}G)", axis=1)
        case "平均ポイント":
            df["内容"] = df.apply(lambda x: f"<>{x["平均ポイント"]:>+7.1f}pt ( {x["通算ポイント"]:>+7.1f}pt /{x["ゲーム数"]:4d}G)", axis=1)
        case "平均収支":
            df["内容"] = df.apply(lambda x: f"<>{x["平均素点"] - 25000:>6.0f}点 ({x["平均素点"]:>6.0f}点 /{x["ゲーム数"]:4d}G)", axis=1)
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
            df["内容"] = df.apply(lambda x: f"<>{x["最大素点"]:>6.0f}点 ({x["最大獲得ポイント"]:>+7.1f}pt)", axis=1)
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
        df (pd.DataFrame): データ

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

    match title:
        case "役満和了":
            df["表示"] = df.apply(lambda x: f"{x["和了役"]}： {x["回数"]} 回", axis=1)
        case "卓外ポイント":
            df["表示"] = df.apply(lambda x: f"{x["内容"]}： {x["回数"]} 回 ({x["ポイント合計"]:.1f}pt)".replace("-", "▲"), axis=1)
        case "その他":
            df["表示"] = df.apply(lambda x: f"{x["内容"]}： {x["回数"]} 回", axis=1)

    tbl = tabulate(df.filter(items=["表示"]).values, showindex=False).splitlines()[1:-1]
    return {"0": textwrap.indent("\n".join(tbl), "\t" * indent)}
