import os

import pandas as pd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.function as f
import lib.database as d
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def point_plot(argument, command_option):
    """
    ポイント推移グラフを生成する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    total_game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    # データ収集
    params = f.configure.get_parameters(argument, command_option)
    total_game_count, target_data, df = _data_collection(argument, command_option, params)

    if target_data.empty: # 描写対象が0人の場合は終了
        return(len(target_data), f.message.no_hits(argument, command_option))

    # 集計
    pivot = pd.pivot_table(df, index = "playtime", columns = "プレイヤー名", values = "point_sum").ffill()
    pivot = pivot.reindex(target_data["プレイヤー名"].to_list(), axis = "columns") # 並び替え

    # グラフ生成
    args = {
        "total_game_count": total_game_count,
        "target_data": target_data,
        "xlabel_text": f"ゲーム終了日時（{total_game_count} ゲーム）",
        "ylabel_text": "累積ポイント",
    }
    if params["target_count"] == 0:
        args["title_text"] = f"ポイント推移 ({params['starttime_hm']} - {params['endtime_hm']})"
    else:
        args["title_text"] = f"ポイント推移 (直近 {params['target_count']} ゲーム)"

    save_file = _graph_generation(pivot, **args)

    # X軸修正
    plt.axhline(y = 0, linewidth = 0.5, ls = "dashed", color = "grey")

    # Y軸修正
    ylocs, ylabs = plt.yticks()
    new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
    plt.yticks(ylocs[1:-1], new_ylabs[1:-1])

    plt.savefig(save_file, bbox_inches = "tight")

    return(total_game_count, save_file)


def rank_plot(argument, command_option):
    """
    順位変動グラフを生成する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    total_game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    # データ収集
    params = f.configure.get_parameters(argument, command_option)
    total_game_count, target_data, df = _data_collection(argument, command_option, params)

    if target_data.empty: # 描写対象が0人の場合は終了
        return(len(target_data), f.message.no_hits(argument, command_option))

    # 集計
    pivot = pd.pivot_table(df, index = "playtime", columns = "プレイヤー名", values = "point_sum").ffill()
    pivot = pivot.reindex(target_data["プレイヤー名"].to_list(), axis = "columns") # 並び替え
    pivot = pivot.rank(method = "dense", ascending = False, axis = 1)

    # グラフ生成
    args = {
        "total_game_count": total_game_count,
        "target_data": target_data,
        "xlabel_text": f"ゲーム終了日時（{total_game_count} ゲーム）",
        "ylabel_text": "順位 (累積ポイント順)",
    }
    if params["target_count"] == 0:
        args["title_text"] = f"順位変動 ({params['starttime_hm']} - {params['endtime_hm']})"
    else:
        args["title_text"] = f"順位変動 (直近 {params['target_count']} ゲーム)"

    save_file = _graph_generation(pivot, **args)

    # Y軸修正
    plt.yticks(
        list(range(len(target_data) + 1 ))[1::2],
        list(range(len(target_data) + 1 ))[1::2]
    )
    plt.gca().invert_yaxis()

    plt.savefig(save_file, bbox_inches = "tight")

    return(total_game_count, save_file)


def _data_collection(argument:list, command_option:dict, params:dict):
    """
    データ収集
    """

    # データ収集
    command_option["fourfold"] = True # 直近Nは4倍する(縦持ちなので4人分)
    total_game_count, _, _ = d.aggregate.game_count(argument, command_option)
    df = d.aggregate.personal_gamedata(argument, command_option)
    target_data = pd.DataFrame()

    if df.empty:
        return(total_game_count, target_data, df)

    target_data["プレイヤー名"] = df.groupby("name").last()["プレイヤー名"]
    target_data["last_point"] = df.groupby("name").last()["point_sum"]
    target_data["game_count"] = df.groupby("name").max()["count"]

    # 足切り
    target_list = list(target_data.query("game_count >= @params['stipulated']").index)
    target_data = target_data.query("name == @target_list").copy()
    df = df.query("name == @target_list").copy()

    # 順位付け
    target_data["position"] = target_data["last_point"].rank(ascending = False).astype(int)

    return(total_game_count, target_data.sort_values("position"), df)


def _graph_generation(df:pd.DataFrame, **kwargs):
    """
    グラフ生成共通処理
    """

    f.common.set_graph_font(plt, fm)
    save_file = os.path.join(g.work_dir, "graph.png")

    g.logging.info(f"plot data:\n{df}")

    # 凡例
    legend_text = []
    for _,v in kwargs["target_data"].iterrows():
        legend_text.append("{}位：{} ({}pt / {}G)".format(
            v["position"], v["プレイヤー名"],
            "{:+.1f}".format(v["last_point"]).replace("-", "▲"), v["game_count"],
        ))

    plt.style.use("ggplot")

    df.plot(
        figsize = (8, 6),
        xlabel = kwargs["xlabel_text"],
        ylabel = kwargs["ylabel_text"],
        marker = "." if len(df) < 50 else None,
    )

    plt.legend(
        legend_text,
        bbox_to_anchor = (1, 1),
        loc = "upper left",
        borderaxespad = 0.5,
        ncol = int(len(kwargs["target_data"]) / 30 + 1),
    )

    plt.title(
        kwargs["title_text"],
        fontsize = 16,
    )

    plt.xticks(
        list(range(len(df)))[::int(len(df) / 25) + 1],
        list(df.index)[::int(len(df) / 25) + 1],
        rotation = 45,
        ha = "right",
    )

    return(save_file)
