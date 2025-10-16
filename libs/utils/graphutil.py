"""
libs/utils/graphutil.py
"""

import logging

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import use

import libs.global_value as g


def setup():
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


def gen_xlabel(game_count: int) -> str:
    """X軸ラベル生成

    Args:
        game_count (int): ゲーム数

    Returns:
        str: X軸ラベル
    """

    if g.params.get("target_count"):
        xlabel = f"直近 {game_count} ゲーム"
    else:
        xlabel = f"集計日（{game_count} ゲーム）"
        match g.params.get("collection"):
            case "daily":
                xlabel = f"集計日（{game_count} ゲーム）"
            case "monthly":
                xlabel = f"集計月（{game_count} ゲーム）"
            case "yearly":
                xlabel = f"集計年（{game_count} ゲーム）"
            case "all":
                xlabel = f"ゲーム数：{game_count} ゲーム"
            case _:
                if g.params.get("search_word"):
                    xlabel = f"ゲーム数：{game_count} ゲーム"
                else:
                    xlabel = f"ゲーム終了日時（{game_count} ゲーム）"

    return xlabel


def x_rotation(n: int) -> int:
    """X軸目盛の傾き

    Args:
        n (int): X軸のデータ数

    Returns:
        int: 傾き
    """

    thresholds = [
        (3, 0),
        (15, 30),
        (40, 45),
        (float("inf"), -90),
    ]

    for limit, angle in thresholds:
        if n <= limit:
            break

    return angle
