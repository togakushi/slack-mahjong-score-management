import logging
import math
import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)


def plot():
    """
    レーティング推移グラフを生成する

    Returns
    -------
    game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    plt.close()
    # データ収集
    game_info = d.aggregate.game_info()
    df_ratings = d.aggregate.calculation_rating()

    if df_ratings.empty:
        return (0, f.message.no_hits())

    # 足切り
    if g.opt.stipulated == 0:  # 規定打数が指定されない場合はレートから計算
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
    df_dropped = df_ratings.dropna(axis=1, thresh=g.opt.stipulated).ffill()

    # ゲスト置換
    for player in df_dropped.columns:
        if player not in g.member_list:
            if g.opt.unregistered_replace:
                df_dropped = df_dropped.drop(columns=[player])
            else:
                df_dropped = df_dropped.rename(
                    columns={
                        player: c.member.name_replace(player, add_mark=True)
                    }
                )

    # 並び変え
    sorted_columns = df_dropped.iloc[-1].sort_values(ascending=False).index
    df_sorted = df_dropped[sorted_columns]

    new_index = {}
    for x in df_sorted[1:].index:
        new_index[x] = x.replace("-", "/")
    df_sorted = df_sorted.rename(index=new_index)

    # --- グラフ生成
    f.common.graph_setup(plt, fm)

    save_file = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "rating.png",
    )

    title_text = f"レーティング推移 ({g.prm.starttime_hm} - {g.prm.endtime_hm})"

    legend_text = []
    count = 1
    for name, rate in df_sorted.iloc[-1].items():
        legend_text.append(f"{count:2d}位： {name} （{rate:.1f}）")
        count += 1

    # ---
    df_sorted.plot(
        figsize=(21, 7),
        xlabel=f"集計日（総ゲーム数：{game_info['game_count']}）",
        ylabel="レート",
        marker="." if len(df_sorted) < 50 else None,
    )
    plt.title(title_text, fontsize=16)
    plt.legend(
        legend_text,
        bbox_to_anchor=(1, 1),
        loc="upper left",
        borderaxespad=0.5,
        ncol=int(len(sorted_columns) / 25 + 1),
    )
    plt.xticks(
        list(range(len(df_sorted)))[1::int(len(df_sorted) / 25) + 1],
        list(df_sorted.index)[1::int(len(df_sorted) / 25) + 1],
        rotation=45,
        ha="right",
    )
    plt.axhline(y=1500, linewidth=0.5, ls="dashed", color="grey")

    plt.savefig(save_file, bbox_inches="tight")

    return (len(df_sorted), save_file)