"""
libs/commands/graph/entry.py
"""

import logging

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import use

import libs.global_value as g
from integrations.protocols import MessageParserProtocol
from libs.commands import graph
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """グラフ生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.data.status != "message_append":
        return

    m.data.command_type = "graph"
    g.params = dictutil.placeholder(g.cfg.graph, m)

    if len(g.params["player_list"]) == 1:  # 対象がひとり
        if g.params.get("statistics"):
            graph.personal.statistics_plot(m)
        else:
            graph.personal.plot(m)
    else:  # 対象が複数
        if g.params.get("rating"):  # レーティング
            graph.rating.plot(m)
        else:
            if g.params.get("order"):
                graph.summary.rank_plot(m)
            else:
                graph.summary.point_plot(m)


def graph_setup() -> None:
    """グラフ設定初期化"""

    pd.options.plotting.backend = g.adapter.conf.plotting_backend
    match g.adapter.conf.plotting_backend:
        case "plotly":
            return

    plt.close()
    use(backend="agg")
    mlogger = logging.getLogger("matplotlib")
    mlogger.setLevel(logging.WARNING)

    # スタイルの適応
    if (style := g.cfg.setting.graph_style) not in plt.style.available:
        style = "ggplot"
    plt.style.use(style)

    # フォント再設定
    for x in ("family", "serif", "sans-serif", "cursive", "fantasy", "monospace"):
        if f"font.{x}" in plt.rcParams:
            plt.rcParams[f"font.{x}"] = ""

    fm.fontManager.addfont(g.cfg.setting.font_file)
    font_prop = fm.FontProperties(fname=g.cfg.setting.font_file)
    plt.rcParams["font.family"] = font_prop.get_name()

    # グリッド線
    if not plt.rcParams["axes.grid"]:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.alpha"] = 0.3
        plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["axes.axisbelow"] = True
