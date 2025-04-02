"""
lib/command/results/ranking.py
"""

import os
import re
from typing import Any, Tuple

import pandas as pd
from tabulate import tabulate

import lib.global_value as g
from lib import database as d
from lib import function as f


def main():
    """ランキングをslackにpostする
    """

    g.opt.initialization("ranking", g.msg.argument)
    g.prm.update(g.opt)

    msg1, msg2 = aggregation()
    res = f.slack_api.post_message(msg1)
    if msg2:
        f.slack_api.post_multi_message(msg2, res["ts"])


def aggregation() -> Tuple[str, Any]:
    """ランキングデータを生成

    Returns:
        Tuple[str, Any]: 集計結果
            - str: ランキングの集計情報
            - dict | Any: 各ランキングの情報
    """

    # --- データ取得
    game_info = d.aggregate.game_info()
    if game_info["game_count"] == 0:  # 結果が0件のとき
        return (f.message.reply(message="no_hits"), None)

    g.prm.stipulated_update(g.opt, game_info["game_count"])
    result_df = d.common.read_data(os.path.join(g.script_dir, "lib/queries/ranking/aggregate.sql"))
    if result_df.empty:
        return (f.message.reply(message="no_hits"), None)

    df = pd.merge(
        result_df, d.aggregate.ranking_record2(),
        on=["name", "name"],
        suffixes=["", "_x"]
    )

    # --- 集計
    data: dict = {}

    # ゲーム参加率
    df["participation_rate"] = df["game_count"] / game_info["game_count"]
    df["rank"] = df["participation_rate"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["participation_rate"]:>7.2%} ({row["game_count"]:3d}G / {game_info["game_count"]:4d}G)", axis=1)
    data["ゲーム参加率"] = table_conversion(df)

    # 通算ポイント
    df["rank"] = df["point_sum"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["point_sum"]:>+7.1f}pt ({row["game_count"]:3d}G)", axis=1)
    data["通算ポイント"] = table_conversion(df)

    # 平均ポイント
    df["rank"] = df["point_avg"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["point_avg"]:>+7.1f}pt ({row["point_sum"]:>+7.1f}pt / {row["game_count"]:3d}G)", axis=1)
    data["平均ポイント"] = table_conversion(df)

    # 平均収支
    df["rank"] = df["rpoint_avg"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["rpoint_avg"] - 25000:>6.0f}点 ({row["rpoint_avg"]:>6.0f}点 / {row["game_count"]:3d}G)", axis=1)
    data["平均収支"] = table_conversion(df)

    # トップ率
    df["rank"] = df["rank1_rate"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["rank1_rate"]:>7.2%} ({row["rank1"]:3d} / {row["game_count"]:3d}G)", axis=1)
    data["トップ率"] = table_conversion(df)

    # 連対率
    df["rank"] = df["top2_rate"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["top2_rate"]:>7.2%} ({row["top2"]:3d} / {row["game_count"]:3d}G)", axis=1)
    data["連対率"] = table_conversion(df)

    # ラス回避率
    df["rank"] = df["top3_rate"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["top3_rate"]:>7.2%} ({row["top3"]:3d} / {row["game_count"]:3d}G)", axis=1)
    data["ラス回避率"] = table_conversion(df)

    # トビ率
    df["rank"] = df["flying_rate"].rank(ascending=True, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["flying_rate"]:>7.2%} ({row["flying"]:3d} / {row["game_count"]:3d}G)", axis=1)
    data["トビ率"] = table_conversion(df)

    # 平均順位
    df["rank"] = df["rank_avg"].rank(ascending=True, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["rank_avg"]:>4.2f} ({row["rank_dist"]})", axis=1)
    data["平均順位"] = table_conversion(df)

    # 役満和了率
    df["rank"] = df["gs_rate"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["gs_rate"]:>7.2%} ({row["gs_count"]:3d} / {row["game_count"]:3d}G)", axis=1)
    data["役満和了率"] = table_conversion(df, ["gs_count", 1])

    # 最大素点
    df["rank"] = df["rpoint_max"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["rpoint_max"]:>6.0f}点 ({row["point_max"]:>+7.1f}pt)", axis=1)
    data["最大素点"] = table_conversion(df)

    # 連続トップ
    df["rank"] = df["c_top"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["c_top"]:>2d}連続 ({row["game_count"]:3d}G)", axis=1)
    data["連続トップ"] = table_conversion(df, ["c_top", 2])

    # 連続連対
    df["rank"] = df["c_top2"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["c_top2"]:>2d}連続 ({row["game_count"]:3d}G)", axis=1)
    data["連続連対"] = table_conversion(df, ["c_top2", 2])

    # 連続ラス回避
    df["rank"] = df["c_top3"].rank(ascending=False, method="dense").astype("int")
    df["disp"] = df.apply(lambda row: f"<>{row["c_top3"]:>2d}連続 ({row["game_count"]:3d}G)", axis=1)
    data["連続ラス回避"] = table_conversion(df, ["c_top3", 2])

    # --- 表示
    if g.opt.individual:  # 個人集計
        msg = "\n*【ランキング】*\n"
    else:  # チーム集計
        msg = "\n*【チームランキング】*\n"

    msg += f.message.header(game_info, "", 1)

    for key in list(data.keys()):
        if key in g.cfg.dropitems.ranking:  # 非表示項目
            data.pop(key)
            continue

        if key in data:  # 対象者がいなければ項目を削除
            if not data[key]:
                data.pop(key)
                continue

        data[key] = f"*{key}*\n" + data[key]

    return (msg, data)


def table_conversion(df: pd.DataFrame, threshold: list | None = None) -> str:
    """テーブル変換

    Args:
        df (pd.DataFrame): 変換対象データ
        threshold (list | None, optional): 非表示にする閾値. Defaults to None.

    Returns:
        str: 作成したテーブル
    """

    if isinstance(threshold, list):
        df = df.query(f"{threshold[0]} >= @threshold[1]").copy()

    if df.empty:
        return ("")

    df.sort_values(by=["rank", "game_count"], ascending=[True, False], inplace=True)
    tbl = tabulate(df.filter(items=["rank", "name", "disp"]).values)
    tbl = re.sub(r"( *[0-9]+)\s(.*)<>(.*)", r"\1:\2\3", tbl)
    tbl = "\n".join(tbl.splitlines()[1:-1]).replace(" -", "▲")
    tbl = f"\n```\n{tbl}\n```\n"

    return (tbl)
