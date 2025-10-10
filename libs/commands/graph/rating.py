"""
libs/commands/graph/rating.py
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import plotly.express as px  # type: ignore

import libs.global_value as g
from libs.data import aggregate, loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.utils import formatter, graphutil, textutil

if TYPE_CHECKING:
    import pandas as pd

    from integrations.protocols import MessageParserProtocol


def plot(m: "MessageParserProtocol"):
    """レーティング推移グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- データ収集
    game_info = GameInfo()
    df_ratings = aggregate.calculation_rating()

    if df_ratings.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        m.status.result = False
        return

    # 足切り
    df_count = loader.read_data("SUMMARY_GAMEDATA").filter(
        items=["name", "count"]
    ).set_index("name").query("count >= @g.params['stipulated']")
    df_dropped = df_ratings.filter(items=df_count.index.to_list())

    # 並び変え
    df_sorted = df_dropped[df_dropped.iloc[-1].sort_values(ascending=False).index]

    new_index = {}
    for x in df_sorted[1:].index:
        new_index[x] = str(x).replace("-", "/")
    df_sorted = df_sorted.rename(index=new_index)

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df_sorted.columns.to_list())
        df_sorted = df_sorted.rename(columns=mapping_dict)

    if df_sorted.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        m.status.result = False
        return

    # --- グラフ生成
    m.post.headline = {"レーティング推移グラフ": message.header(game_info, m)}
    match g.adapter.conf.plotting_backend:
        case "matplotlib":
            save_file = textutil.save_file_path("rating", ".png", True)
            _graph_generation(game_info, df_sorted, save_file)
        case "plotly":
            save_file = textutil.save_file_path("rating", ".html", True)
            _graph_generation_plotly(game_info, df_sorted, save_file)

    m.post.file_list = [{"レーティング推移": save_file}]


def _graph_generation(game_info: GameInfo, df: "pd.DataFrame", save_file: str):
    """レーティング推移グラフ生成(matplotlib)

    Args:
        game_info (GameInfo): ゲーム情報
        df (pd.DataFrame): 描写データ
        save_file (str): 保存先ファイル名
    """

    graphutil.setup()
    title_text, xlabel_text = _graph_title(game_info)
    legend_text = []
    count = 1
    for name, rate in df.iloc[-1].items():
        legend_text.append(f"{count:2d}位：{name} （{rate:.1f}）")
        count += 1

    # ---
    df.plot(
        figsize=(21, 7),
        xlabel=xlabel_text,
        ylabel="レート",
        marker="." if len(df) < 20 else None,
        linewidth=2 if len(df) < 40 else 1,
    )
    plt.title(title_text, fontsize=16)
    plt.legend(
        legend_text,
        bbox_to_anchor=(1, 1),
        loc="upper left",
        borderaxespad=0.5,
        ncol=int(len(df.columns) / 25 + 1),
    )
    plt.xticks(
        list(range(len(df)))[1::int(len(df) / 25) + 1],
        list(df.index)[1::int(len(df) / 25) + 1],
        rotation=45,
        ha="right",
    )
    plt.axhline(y=1500, linewidth=0.5, ls="dashed", color="grey")

    plt.savefig(save_file, bbox_inches="tight")


def _graph_generation_plotly(game_info: GameInfo, df: "pd.DataFrame", save_file: str):
    """レーティング推移グラフ生成(plotly)

    Args:
        game_info (GameInfo): ゲーム情報
        df (pd.DataFrame): 描写データ
        save_file (str): 保存先ファイル名
    """

    # グラフタイトル/ラベル
    title_text, xlabel_text = _graph_title(game_info)
    # 凡例用テキスト
    legend_text = []
    count = 1
    for name, rate in df.iloc[-1].items():
        legend_text.append(f"{count:2d}位：{name} （{rate:.1f}）")
        count += 1

    df.rename(index={"initial_rating": ""}, inplace=True)
    df.columns = legend_text

    fig = px.line(df, markers=True)

    # グラフレイアウト調整
    fig.update_layout(
        width=1280,
        height=800,
        title={
            "text": title_text,
            "font": {"size": 30},
            "x": 0.1,
        },
        xaxis_title={
            "text": xlabel_text,
            "font": {"size": 18},
        },
        yaxis_title={
            "text": "レート",
            "font": {"size": 18},
        },
        legend_title=None,
    )

    # 軸/目盛調整
    if all(df.count() > 20):
        fig.update_traces(mode="lines")  # マーカー非表示
    if len(fig.data) > 40:
        fig.update_traces(mode="lines", line={"width": 1})  # ラインを細く

    fig.write_html(save_file, full_html=False)


def _graph_title(game_info: GameInfo) -> tuple[str, str]:
    """グラフタイトル/ラベル生成

    Args:
        game_info (GameInfo): ゲームデータ

    Returns:
        tuple[str, str]: タイトル文字列
    """

    match g.params.get("collection"):
        case "daily":
            kind = "ymd_o"
            xlabel_text = f"集計日（総ゲーム数：{game_info.count} ゲーム）"
        case "monthly":
            kind = "jym_o"
            xlabel_text = f"集計月（総ゲーム数：{game_info.count} ゲーム）"
        case "yearly":
            kind = "jy_o"
            xlabel_text = f"集計年（総ゲーム数：{game_info.count} ゲーム）"
        case "all":
            kind = "ymdhm"
            xlabel_text = f"総ゲーム数：{game_info.count} ゲーム"
        case _:
            kind = "ymdhm"
            xlabel_text = f"ゲーム終了日時（総ゲーム数：{game_info.count} ゲーム）"

    title_text = f"レーティング推移 ({compose.text_item.date_range(kind)})"

    return title_text, xlabel_text
