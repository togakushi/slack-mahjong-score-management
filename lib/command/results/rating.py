import math

import pandas as pd

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def aggregation():
    """
    レーティングを集計して返す
    """

    # ゲスト強制除外
    g.opt.guest_skip = True

    # データ収集
    game_info = d.aggregate.game_info()
    df_ratings = d.aggregate.calculation_rating()
    df_results = d.aggregate.simple_results()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final["count"] = df_ratings.count() - 1
    final.columns = ["rate", "count"]
    final["name"] = final.copy().index

    if g.opt.stipulated == 0:  # 規定打数が指定されない場合はレートから計算
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)

    # 足切り
    final = final.query("count >= @g.opt.stipulated")
    df_results = df_results.query("count >= @g.opt.stipulated")

    df = pd.merge(df_results, final, on=["name", "count"]).sort_values(by="rate", ascending=False)

    # ゲスト置換
    if g.opt.unregistered_replace:
        for player in final.index:
            if player not in g.member_list:
                final = final.copy().drop(player)
                df = df.copy().drop(player)
    df["名前"] = df["name"].copy().apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    # 計算
    df["得点偏差"] = (df["rpoint_avg"] - 25000) / df["rpoint_avg"].std(ddof=0) * 10 + 50
    df["順位偏差"] = (df["rank_avg"] - 2.5) / df["rank_avg"].std(ddof=0) * -10 + 50

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    headline = "*【レーティング】*\n"
    headline += f.message.header(game_info, add_text, 1)

    df = df.rename(columns={
        "rate": "レート",
        "rank_dist": "順位分布",
        "rank_avg": "平均順位",
        "rpoint_avg": "平均素点",
    }).copy()

    msg = df.filter(
        items=[
            "名前", "レート", "平均順位", "順位偏差", "平均素点", "得点偏差", "順位分布"
        ]
    ).to_markdown(
        index=False,
        tablefmt="simple",
        numalign="right",
        floatfmt=("", ".1f", ".2f", ".0f", ".1f", ".0f", "")
    )
    msg = f"```\n{msg}\n```\n"

    return (headline, msg)