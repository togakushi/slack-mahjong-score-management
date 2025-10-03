"""
libs/commands/graph/rating.py
"""

import os
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

import libs.global_value as g
from cls.types import GameInfoDict
from libs.commands.graph.entry import graph_setup
from libs.data import aggregate
from libs.functions import compose, message
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def plot(m: MessageParserProtocol) -> bool:
    """レーティング推移グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ

    """

    # データ収集
    game_info: GameInfoDict = aggregate.game_info()
    df_ratings = aggregate.calculation_rating()

    if df_ratings.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        return False

    # 足切り
    df_dropped = df_ratings.dropna(axis=1, thresh=g.params["stipulated"]).ffill()

    # 並び変え
    sorted_columns = df_dropped.iloc[-1].sort_values(ascending=False).index
    df_sorted = df_dropped[sorted_columns]

    new_index = {}
    for x in df_sorted[1:].index:
        new_index[x] = str(x).replace("-", "/")
    df_sorted = df_sorted.rename(index=new_index)

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df_sorted.columns.to_list())
        df_sorted = df_sorted.rename(columns=mapping_dict)

    # --- グラフ生成
    graph_setup()
    save_file = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.params["filename"]}.png" if g.params.get("filename") else "rating.png",
    )

    title_text = f"レーティング推移 ({compose.text_item.date_range("ymdhm")})"

    legend_text = []
    count = 1
    for name, rate in df_sorted.iloc[-1].items():
        legend_text.append(f"{count:2d}位：{name} （{rate:.1f}）")
        count += 1

    # ---
    df_sorted.plot(
        figsize=(21, 7),
        xlabel=f"集計日（総ゲーム数：{game_info["game_count"]}）",
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

    m.post.file_list = [{"レーティング推移": save_file}]
    return True
