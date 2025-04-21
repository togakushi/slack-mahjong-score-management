"""
libs/commands/results/summary.py
"""

import os
import re

import pandas as pd

import libs.global_value as g
from cls.types import GameInfoDict
from libs.data import aggregate
from libs.data.loader import read_data
from libs.functions import message
from libs.utils import formatter


def aggregation():
    """各プレイヤーの通算ポイントを表示

    Returns:
        Tuple[str, dict, dict]
        - str: ヘッダ情報
        - dict: 集計データ
        - dict: 生成ファイル情報
    """

    # --- データ収集
    game_info: GameInfoDict = aggregate.game_info()
    df_summary = aggregate.game_summary(drop_items=["rank_distr2"])
    df_game = read_data(os.path.join(g.cfg.script_dir, "libs/queries/summary/details.sql"))
    df_grandslam = df_game.query("grandslam == grandslam")

    if g.params.get("anonymous"):
        col = "team"
        if g.params.get("individual"):
            col = "name"
        mapping_dict = formatter.anonymous_mapping(df_game["name"].unique().tolist())
        df_game["name"] = df_game["name"].replace(mapping_dict)
        df_summary[col] = df_summary[col].replace(mapping_dict)
        df_grandslam["name"] = df_grandslam["name"].replace(mapping_dict)

    df_summary = formatter.df_rename(df_summary)

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    if g.params.get("individual"):  # 個人集計
        headline = "*【成績サマリ】*\n"
        column_name = "名前"
    else:  # チーム集計
        headline = "*【チーム成績サマリ】*\n"
        column_name = "チーム"

    if not g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        add_text = f" / トバされた人（延べ）：{df_summary["トビ"].sum()} 人"

    headline += message.header(game_info, add_text, 1)

    if df_summary.empty:
        return (headline, {}, {})

    # --- 集計結果
    msg: dict = {}
    msg_memo: str = memo_count(df_game)

    if not g.params.get("score_comparisons"):  # 通常表示
        header_list: list = [column_name, "通算", "平均", "順位分布", "トビ"]
        filter_list: list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "トビ"]
        if g.cfg.config["mahjong"].getboolean("ignore_flying", False):  # トビカウントなし
            header_list.remove("トビ")
            filter_list.remove("トビ")
    else:  # 差分表示
        df_grandslam = df_grandslam[:0]  # 非表示のため破棄
        msg_memo = ""  # 非表示のため破棄
        header_list = ["#", column_name, "通算", "順位差", "トップ差"]
        filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]

    # --- メッセージ整形
    step: int = 40
    step_count: list = []
    print_df = df_summary.filter(items=header_list)
    floatfmt = formatter.floatfmt_adjust(print_df)
    last_line = len(print_df)

    for i in range(int(last_line / step + 1)):  # step行毎に分割
        s_line = i * step
        e_line = (i + 1) * step

        if last_line - e_line < step / 2:  # 最終ブロックがstep/2で収まるならまとめる
            step_count.append((s_line, last_line))
            break
        step_count.append((s_line, e_line))

    for s_line, e_line in step_count:
        t = print_df[s_line:e_line].to_markdown(
            index=False,
            tablefmt="simple",
            numalign="right",
            maxheadercolwidths=8,
            floatfmt=floatfmt,
        ).replace("   nan", "******")
        msg[s_line] = "```\n" + re.sub(r"  -([0-9]+)", r" ▲\1", t) + "\n```\n"  # マイナスを記号に置換

    # メモ追加
    if msg_memo:
        msg["メモ"] = msg_memo

    # --- ファイル出力
    df_summary = df_summary.filter(items=filter_list).fillna("*****")
    df_grandslam = df_grandslam.filter(
        items=["playtime", "grandslam", "name"]
    ).rename(
        columns={
            "playtime": "日時",
            "grandslam": "和了役",
            "name": "和了者",
        }
    )

    prefix_summary = "summary"
    prefix_yakuman = "yakuman"
    if g.params.get("filename"):
        prefix_summary = f"{g.params["filename"]}"
        prefix_yakuman = f"{g.params["filename"]}_yakuman"

    match g.params.get("format", "default").lower().lower():
        case "csv":
            file_list = {
                "集計結果": formatter.save_output(df_summary, "csv", f"{prefix_summary}.csv", headline),
                "役満和了": formatter.save_output(df_grandslam, "csv", f"{prefix_yakuman}.csv", headline),
            }
        case "text" | "txt":
            file_list = {
                "集計結果": formatter.save_output(df_summary, "txt", f"{prefix_summary}.txt", headline),
                "役満和了": formatter.save_output(df_grandslam, "txt", f"{prefix_yakuman}.txt", headline),
            }
        case _:
            file_list = {}

    return (headline, msg, file_list)


def memo_count(df_game: pd.DataFrame) -> str:
    """メモ集計

    Args:
        df_game (pd.DataFrame): ゲーム情報

    Returns:
        str: 集計結果
    """

    # データ収集
    df_grandslam = df_game.query("grandslam == grandslam")
    match g.cfg.undefined_word:
        case 1:
            df_regulations = df_game.query("regulation == regulation and (type == 1 or type != type)")
            df_wordcount = df_game.query("regulation == regulation and (type == 2 or type == type)")
        case 2:
            df_regulations = df_game.query("regulation == regulation and (type == 1 or type == type)")
            df_wordcount = df_game.query("regulation == regulation and (type == 2 or type != type)")
        case _:
            df_regulations = df_game.query("regulation == regulation and type == 1")
            df_wordcount = df_game.query("regulation == regulation and type == 2")

    # メモ表示
    memo_grandslam = ""
    if not df_grandslam.empty:
        for _, v in df_grandslam.iterrows():
            if not g.params.get("guest_skip") and v["name"] == g.cfg.member.guest_name:  # ゲストなし
                continue
            memo_grandslam += f"\t{v["playtime"].replace("-", "/")}：{v["grandslam"]} （{v["name"]}）\n"
    if memo_grandslam:
        memo_grandslam = f"\n*【役満和了】*\n{memo_grandslam}"

    memo_regulation = ""
    if not df_regulations.empty:
        for _, v in df_regulations.iterrows():
            if not g.params.get("guest_skip") and v["name"] == g.cfg.member.guest_name:  # ゲストなし
                continue
            memo_regulation += f"\t{v["playtime"].replace("-", "/")}：{v["regulation"]} {str(v["ex_point"]).replace("-", "▲")}pt（{v["name"]}）\n"
    if memo_regulation:
        memo_regulation = f"\n*【卓外ポイント】*\n{memo_regulation}"

    memo_wordcount = ""
    if not df_wordcount.empty:
        for _, v in df_wordcount.iterrows():
            if not g.params.get("guest_skip") and v["name"] == g.cfg.member.guest_name:  # ゲストなし
                continue
            memo_wordcount += f"\t{v["playtime"].replace("-", "/")}：{v["regulation"]} （{v["name"]}）\n"
    if memo_wordcount:
        memo_wordcount = f"\n*【その他】*\n{memo_wordcount}"

    return (memo_grandslam + memo_regulation + memo_wordcount).strip()
