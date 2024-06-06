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

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]

    # --- データ収集 ToDo: 仮置き換え
    params = f.configure.get_parameters(argument, command_option)
    total_game_count, _, _ = d.aggregate.game_count(argument, command_option)
    df = d.aggregate.personal_gamedata(argument, command_option)
    target_player = params["player_name"]
    playtime = df["playtime"].to_list()
    point = df["point"].to_list()
    point_sum = df["point_sum"].to_list()
    point_avg = df["point_avg"].to_list()
    rank = df["rank"].to_list()
    rank_avg = df["rank_avg"].to_list()

    if total_game_count == 0:
        return(total_game_count, f.message.no_hits(argument, command_option))

    ### グラフ生成 ###
    save_file = os.path.join(g.work_dir, "graph.png")
    # グラフフォント設定
    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    plt.style.use("ggplot")

    # サイズ、表記調整
    fig = plt.figure(figsize = (10, 8))
    rotation = 45
    position = "right"

    if total_game_count > 10:
        rotation = 60
    if total_game_count > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(total_game_count / 5), 8))
        rotation = 90
        position = "center"
    if total_game_count == 1:
        rotation = 0
        position = "center"

    _xlabel = f"ゲーム終了日時（{total_game_count} ゲーム）"
    if params["target_count"] == 0:
        title_text = f"『{target_player}』の成績 ({params['starttime_hm']} - {params['endtime_hm']})"
    else:
        title_text = f"『{target_player}』の成績 (直近 {total_game_count} ゲーム)"

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])
    fig.suptitle(title_text, fontsize = 12)

    # 累積推移
    point_ax = fig.add_subplot(grid[0])
    point_ax.set_ylabel("ポイント")
    point_ax.set_xlim(-1, total_game_count)
    point_ax.hlines(y = 0, xmin = -1, xmax = total_game_count, linewidth = 0.5, linestyles="dashed", color = "grey")
    point_ax.plot(playtime, point_sum, marker = "o", markersize = 3, label = f"累積ポイント({str(point_sum[-1])}pt)".replace("-", "▲"))
    point_ax.plot(playtime, point_avg, marker = "o", markersize = 3, label = f"平均ポイント({str(point_avg[-1])}pt)".replace("-", "▲"))
    point_ax.bar(playtime, point, color = "dodgerblue", label = f"獲得ポイント")
    point_ax.tick_params(axis = "x", labelsize = 0, labelcolor = "white") # 背景色と同じにして見えなくする
    point_ax.legend(bbox_to_anchor = (1, 1), loc = "upper left", borderaxespad = 0.5)

    ticks = point_ax.get_yticks()
    point_ax.set_yticks(ticks[1:-1])
    new_ticks = [str(int(i)).replace("-", "▲") for i in ticks]
    point_ax.set_yticklabels(new_ticks[1:-1])

    # 順位分布
    rank_ax = fig.add_subplot(grid[1], sharex = point_ax)
    rank_ax.invert_yaxis()
    rank_ax.set_ylabel("順位")
    rank_ax.set_xlabel(_xlabel)
    rank_ax.set_xlim(-1, total_game_count)
    rank_ax.set_ylim(4.2, 0.8)
    rank_ax.hlines(y = 2.5, xmin = -1, xmax = total_game_count, linewidth = 0.5, linestyles="dashed", color = "grey")
    rank_ax.plot(playtime, rank, marker = "o", markersize = 3, label = f"獲得順位")
    rank_ax.plot(playtime, rank_avg, marker = "o", markersize = 3, label = f"平均順位({rank_avg[-1]})")
    rank_ax.legend(bbox_to_anchor = (1, 1), loc = "upper left", borderaxespad = 0.5)

    plt.setp(rank_ax.get_xticklabels(), rotation = rotation, ha = position)
    fig.tight_layout()
    fig.savefig(save_file)
    plt.close()

    return(total_game_count, save_file)
