import pandas as pd

import lib.global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def aggregation():
    """レーティングを集計して返す

    Returns:
        Tuple[str, dict, dict]:
            - str: ヘッダ情報
            - dict: 集計データ
            - dict: 生成ファイルの情報
    """

    # データ収集
    # g.opt.guest_skip = False  # 2ゲスト戦強制取り込み
    game_info = d.aggregate.game_info()
    df_results = d.aggregate.simple_results()
    df_ratings = d.aggregate.calculation_rating()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final["count"] = df_ratings.count() - 1
    final.columns = ["rate", "count"]
    final["name"] = final.copy().index

    # 足切り
    g.prm.stipulated_update(g.opt, game_info["game_count"])
    final = final.query("count >= @g.prm.stipulated")
    df_results = df_results.query("count >= @g.prm.stipulated")

    df = pd.merge(df_results, final, on=["name"]).sort_values(by="rate", ascending=False)

    # ゲスト置換
    df["名前"] = df["name"].copy().apply(
        lambda x: c.member.name_replace(x, add_mark=True)
    )
    if g.opt.unregistered_replace:
        for player in df.itertuples():
            if player.name not in g.member_list:
                df = df.copy().drop(player.Index)

    # 計算
    df["得点偏差"] = (df["rpoint_avg"] - df["rpoint_avg"].mean()) / df["rpoint_avg"].std(ddof=0) * 10 + 50
    df["順位偏差"] = (df["rank_avg"] - df["rank_avg"].mean()) / df["rank_avg"].std(ddof=0) * -10 + 50

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    headline = "*【レーティング】* （実験的な機能）\n"
    headline += f.message.header(game_info, add_text, 1)

    df = df.rename(columns={
        "rate": "レート",
        "rank_dist": "順位分布",
        "rank_avg": "平均順位",
        "rpoint_avg": "平均素点",
    }).filter(
        items=[
            "名前", "レート", "順位分布", "平均順位", "順位偏差", "平均素点", "得点偏差"
        ]
    ).copy()

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

    match g.opt.format.lower():
        case "csv":
            file_list = {
                "レーティング": f.common.save_output(df, "csv", "rating.csv", headline),
            }
        case "text" | "txt":
            file_list = {
                "レーティング": f.common.save_output(df, "txt", "rating.txt", headline),
            }
        case _:
            file_list = {}

    return (headline, msg, file_list)
