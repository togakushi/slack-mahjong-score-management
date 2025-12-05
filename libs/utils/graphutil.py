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


def xticks_parameter(days_list: list) -> dict:
    """X軸(xticks)に渡すパラメータを生成

    Args:
        days_list (list): 日付リスト

    Returns:
        dict: パラメータ
    """

    days_list = [str(x).replace("-", "/") for x in days_list]

    thresholds = [
        # データ数, 傾き, 位置
        (3, 0, "center"),
        (20, -30, "left"),
        (40, -45, "left"),
        (80, -60, "left"),
        (float("inf"), -90, "center"),
    ]

    for limit, rotation, position in thresholds:
        if len(days_list) <= limit:
            break

    return {
        "ticks": list(range(len(days_list)))[:: int(len(days_list) / 25) + 1],
        "labels": days_list[:: int(len(days_list) / 25) + 1],
        "rotation": rotation,
        "ha": position,
    }
