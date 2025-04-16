"""
lib/command/results/rating.py
"""

import os

import pandas as pd

import lib.global_value as g
from cls.types import GameInfoDict
from lib.data import aggregate, loader
from lib.function import message
from lib.utils import formatter


def aggregation():
    """レーティングを集計して返す

    Returns:
        Tuple[str, dict, dict]:
        - str: ヘッダ情報
        - dict: 集計データ
        - dict: 生成ファイルの情報
    """

    # データ収集
    # g.params.update(guest_skip=False)  # 2ゲスト戦強制取り込み
    game_info: GameInfoDict = aggregate.game_info()
    df_results = loader.read_data(os.path.join(g.script_dir, "lib/queries/ranking/results.sql")).set_index("name")
    df_ratings = aggregate.calculation_rating()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final["count"] = df_ratings.count() - 1
    final.columns = ["rate", "count"]
    final["name"] = final.copy().index

    # 足切り
    final = final.query("count >= @g.params['stipulated']")
    df_results = df_results.query("count >= @g.params['stipulated']")

    df = pd.merge(df_results, final, on=["name"]).sort_values(by="rate", ascending=False)

    # 集計対象外データの削除
    if g.params.get("unregistered_replace"):  # 個人戦
        for player in df.itertuples():
            if player.name not in g.member_list:
                df = df.copy().drop(player.Index)

    if not g.params.get("individual"):  # チーム戦
        df = df.copy().query("name != '未所属'")

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    # 計算
    df["point_dev"] = (df["rpoint_avg"] - df["rpoint_avg"].mean()) / df["rpoint_avg"].std(ddof=0) * 10 + 50
    df["rank_dev"] = (df["rank_avg"] - df["rank_avg"].mean()) / df["rank_avg"].std(ddof=0) * -10 + 50

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    headline = "*【レーティング】* （実験的な機能）\n"
    headline += message.header(game_info, add_text, 1)

    df = formatter.df_rename(df.filter(
        items=[
            "name", "rate", "rank_distr", "rank_avg", "rank_dev", "rpoint_avg", "point_dev"
        ]
    ), short=False).copy()

    msg: dict = {}
    table_param: dict = {
        "index": False,
        "tablefmt": "simple",
        "numalign": "right",
        "floatfmt": ["", ".1f", "", ".2f", ".0f", ".1f", ".0f"],
    }

    step = 30
    length = len(df)
    for i in range(int(length / step) + 1):
        s = step * i
        e = step * (i + 1)
        if e + step / 2 > length:
            table = df[s:].to_markdown(**table_param)
            msg[s] = f"```\n{table}\n```\n"
            break

        table = df[s:e].to_markdown(**table_param)
        msg[s] = f"```\n{table}\n```\n"

    prefix_rating = "rating"
    if g.params.get("filename"):
        prefix_rating = f"{g.params["filename"]}"

    match g.params.get("format", "default").lower().lower():
        case "csv":
            file_list = {
                "レーティング": formatter.save_output(df, "csv", f"{prefix_rating}.csv", headline),
            }
        case "text" | "txt":
            file_list = {
                "レーティング": formatter.save_output(df, "txt", f"{prefix_rating}.txt", headline),
            }
        case _:
            file_list = {}

    return (headline, msg, file_list)
