"""
libs/utils/converter.py
"""

import re
import textwrap
from typing import TYPE_CHECKING, Optional, Union, cast

import pandas as pd
from table2ascii import Alignment, PresetStyle, table2ascii
from tabulate import tabulate

import libs.global_value as g
from libs.utils import formatter, textutil

if TYPE_CHECKING:
    from pathlib import Path


def save_output(
    df: pd.DataFrame,
    kind: str,
    filename: str,
    headline: Optional[str] = None,
    suffix: Optional[str] = None,
) -> Union["Path", None]:
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): 描写対象データ
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (Optional[str], optional): 集計情報（ヘッダコメント）. Defaults to None.
        suffix (Optional[str], optional): 保存ファイル名に追加する文字列. Defaults to None.

    Returns:
        Path: 保存したファイルパス
        None: 未知のフォーマットが指定された場合
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
            return None

    # 保存
    save_file = textutil.save_file_path(filename, True)
    if suffix and g.params.get("filename"):
        save_file = save_file.with_name(f"{save_file.stem}_{suffix}{save_file.suffix}")

    with open(save_file, "w", encoding="utf-8") as writefile:
        if headline is not None:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return save_file


def df_to_text_table(df: pd.DataFrame, step: int = 40, index: bool = False) -> dict:
    """DataFrameからテキストテーブルの生成

    Args:
        df (pd.DataFrame): 対象データ
        step (int, optional): 分割行. Defaults to 40.
        index (bool, optional): インデックスを含める. Defaults to False.

    Returns:
        dict: 生成テーブル
    """

    # ヘッダ/位置
    header: list = []
    alignments: list = []
    if index:
        df.reset_index(inplace=True, drop=True)
        df.index += 1
        header.append("")
    for col in df.columns:
        header.append(col)
        match col:
            case "名前" | "プレイヤー名":
                alignments.append(Alignment.LEFT)
            case _:
                alignments.append(Alignment.RIGHT)

    # 表データ
    body: list = []
    data: list = []
    for row in df.to_dict(orient="records"):
        data.clear()
        for k, v in row.items():
            match k:
                case "通算" | "平均" | "平均素点":
                    data.append(f"{v:+.1f}".replace("-", "▲"))
                case "平順" | "平均順位":
                    data.append(f"{v:.2f}")
                case "レート":
                    data.append(f"{v:.1f}")
                case "順位偏差" | "得点偏差":
                    data.append(f"{v:.0f}")
                case _:
                    data.append(str(v).replace("nan", "*****"))
            if index:
                data.insert(0, "")
        body.append(data.copy())

    # 表生成/分割
    my_style = PresetStyle.plain
    my_style.heading_row_sep = "-"
    my_style.heading_row_right_tee = ""
    my_style.heading_row_left_tee = ""

    table_data: dict = {}
    for idx, table_body in enumerate(textutil.split_balanced(body, step)):
        output = table2ascii(
            header=header,
            body=table_body,
            style=my_style,
            cell_padding=0,
            first_col_heading=index,
            alignments=alignments,
        )
        table_data.update({f"{idx}": output})

    return table_data


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
    body: list = []
    alignments: list = []
    match title:
        case "ゲーム参加率":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.ゲーム参加率:>7.2%}",
                    f"({x.ゲーム数:4d}G / {x.集計ゲーム数:4d}G)",
                ])
        case "通算ポイント":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.通算ポイント:>+8.1f}pt".replace("-", "▲"),
                    f"({x.ゲーム数:4d}G)",
                ])
        case "平均ポイント":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.平均ポイント:>+8.1f}pt".replace("-", "▲"),
                    f"({x.通算ポイント:>+8.1f}pt / {x.ゲーム数:4d}G)".replace("-", "▲"),
                ])
        case "平均収支":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.平均収支:>6.0f}点".replace("-", "▲"),
                    f"({x.平均素点:>6.0f}点 / {x.ゲーム数:4d}G)".replace("-", "▲"),
                ])
        case "トップ率":
            df = df.rename(columns={"1位率": "トップ率", "1位数": "トップ数"})
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.トップ率:>7.2%}",
                    f"({x.トップ数:3d} / {x.ゲーム数:4d}G)",
                ])
        case "連対率":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.連対率:>7.2%}",
                    f"({x.連対数:3d} / {x.ゲーム数:4d}G)",
                ])
        case "ラス回避率":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.ラス回避率:>7.2%}",
                    f"({x.ラス回避数:3d} / {x.ゲーム数:4d}G)",
                ])
        case "トビ率":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.トビ率:>7.2%}",
                    f"({x.トビ数:3d} / {x.ゲーム数:4d}G)",
                ])
        case "平均順位":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.平均順位:>4.2f}",
                    f"({x.順位分布})",
                ])
        case "役満和了率":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.役満和了率:>7.2%}",
                    f"({x.役満和了数:3d} / {x.ゲーム数:4d}G)",
                ])
        case "最大素点":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.最大素点:>6.0f}点".replace("-", "▲"),
                    f"({x.最大獲得ポイント:>+8.1f}pt)".replace("-", "▲"),
                ])
        case "連続トップ":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.連続トップ:>2d}連続",
                    f"({x.ゲーム数:4d}G)",
                ])
        case "連続連対":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.連続連対:>2d}連続",
                    f"({x.ゲーム数:4d}G)",
                ])
        case "連続ラス回避":
            alignments = [Alignment.RIGHT, Alignment.LEFT, Alignment.RIGHT, Alignment.LEFT]
            for x in df.itertuples():
                body.append([
                    f"{x.順位}:",
                    x.プレイヤー名,
                    f"{x.連続ラス回避:>2d}連続",
                    f"({x.ゲーム数:4d}G)",
                ])
        case _:
            return {}

    # 整形/分割
    ret: dict = {}
    if step:
        data = textutil.split_balanced(body, step)
        last_block = len(data)
    else:
        last_block = 1

    if last_block == 1:
        output = table2ascii(
            body=body,
            style=PresetStyle.plain,
            cell_padding=0,
            first_col_heading=True,
            alignments=alignments,
        )
        ret.update({title: output})
    else:
        count = 0
        for x in data:
            count += 1
            output = table2ascii(
                body=x,
                style=PresetStyle.plain,
                cell_padding=0,
                first_col_heading=True,
                alignments=alignments,
            )
            ret.update({f"{title} ({count}/{last_block})": output})

    return ret


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
