import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib import gridspec

import lib.function as f
import lib.database as d
from lib.function import global_value as g


mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    """
    個人成績のグラフを生成する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    # データ収集
    command_option["guest_skip"] = command_option["guest_skip2"] # 検索動作を合わせる
    params = f.configure.get_parameters(argument, command_option)
    df = d.aggregate.personal_gamedata(argument, command_option)

    if df.empty:
        return(0, f.message.no_hits(argument, command_option))

    # 最終値（凡例追加用）
    point_sum = "{:+.1f}".format(float(df["point_sum"].iloc[-1])).replace("-", "▲")
    point_avg = "{:+.1f}".format(float(df["point_avg"].iloc[-1])).replace("-", "▲")
    rank_avg = "{:.2f}".format(float(df["rank_avg"].iloc[-1]))

    ### グラフ生成 ###
    f.common.set_graph_font(plt, fm)
    save_file = os.path.join(g.work_dir, "graph.png")

    plt.style.use("ggplot")
    fig = plt.figure(figsize = (12, 8))

    if params["target_count"] == 0:
        title_text = f"『{params['player_name']}』の成績 ({params['starttime_hm']} - {params['endtime_hm']})"
    else:
        title_text = f"『{params['player_name']}』の成績 (直近 {len(df)} ゲーム)"

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])
    point_ax = fig.add_subplot(grid[0])
    rank_ax = fig.add_subplot(grid[1], sharex = point_ax)

    # ---
    df.filter(items = ["point_sum", "point_avg"]).plot.line(
        ax = point_ax,
        ylabel = "ポイント(pt)",
        marker = "." if len(df) < 50 else None,
    )
    df.filter(items = ["point"]).plot.bar(
        ax = point_ax,
        color = "blue",
    )
    point_ax.legend(
        [f"累積ポイント ({point_sum}pt)", f"平均ポイント ({point_avg}pt)", "獲得ポイント"],
        bbox_to_anchor = (1, 1),
        loc = "upper left",
        borderaxespad = 0.5,
    )
    point_ax.axhline(y = 0, linewidth = 0.5, ls = "dashed", color = "grey")

    # Y軸修正
    ylabs = point_ax.get_yticks()[1:-1]
    point_ax.set_yticks(ylabs)
    point_ax.set_yticklabels([str(int(ylab)).replace("-", "▲") for ylab in ylabs])

    # ---
    df.filter(items = ["rank", "rank_avg"]).plot.line(
        ax = rank_ax,
        marker = "." if len(df) < 50 else None,
        yticks = [1, 2, 3, 4],
        ylabel = "順位",
        xlabel = f"ゲーム終了日時（{len(df)} ゲーム）",
    )
    rank_ax.legend(
        ["獲得順位", f"平均順位 ({rank_avg})"],
        bbox_to_anchor = (1, 1),
        loc = "upper left",
        borderaxespad = 0.5,
    )

    rank_ax.set_xticks(list(df.index)[::int(len(df) / 25) + 1])
    rank_ax.set_xticklabels(list(df["playtime"])[::int(len(df) / 25) + 1], rotation = 45, ha = "right")
    rank_ax.axhline(y = 2.5, linewidth = 0.5, ls = "dashed", color = "grey")
    rank_ax.invert_yaxis()

    fig.suptitle(title_text, fontsize = 16)
    fig.tight_layout()
    plt.savefig(save_file, bbox_inches = "tight")

    return(len(df), save_file)
