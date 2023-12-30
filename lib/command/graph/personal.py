import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib import gridspec

import lib.command as c
import lib.function as f
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(starttime, endtime, target_player, target_count, command_option):
    """
    個人成績のグラフを生成する

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    command_option : dict
        コマンドオプション

    Returns
    -------
    int : int
        グラフにプロットしたゲーム数
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]
    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    results = f.search.game_select(starttime, endtime, target_player, target_count, command_option)
    target_player = [c.NameReplace(name, command_option, add_mark = True) for name in target_player] # ゲストマーク付きリストに更新
    g.logging.info(f"target_player(update):  {target_player}")

    ### データ抽出 ###
    game_point = []
    game_rank = []
    game_time = []

    for i in results.keys():
        for wind in g.wind[0:4]:
            if results[i][wind]["name"] in target_player:
                game_time.append(results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"))
                game_point.append(results[i][wind]["point"])
                game_rank.append(results[i][wind]["rank"])

    if len(game_time) == 0:
        return(len(game_time))

    ### 集計 ###
    stacked_point = []
    total_point = 0
    for point in game_point:
        total_point = round(total_point + point, 2)
        stacked_point.append(total_point)

    rank_avg = []
    rank_sum = 0
    for rank in game_rank:
        rank_sum = rank_sum + rank
        rank_avg.append(round(rank_sum / (len(rank_avg) + 1), 2))

    ### グラフ生成 ###
    # --- グラフフォント設定
    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    plt.style.use("ggplot")

    # サイズ、表記調整
    fig = plt.figure(figsize = (10, 8))
    rotation = 45
    position = "right"

    if len(game_time) > 10:
        rotation = 60
    if len(game_time) > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(len(game_time) / 5), 8))
        rotation = 90
        position = "center"
    if len(game_time) == 1:
        rotation = 0
        position = "center"

    _xlabel = f"ゲーム終了日時（{len(game_time)} ゲーム）"
    if target_count == 0:
        title_text = f"『{target_player[0]}』の成績 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
    else:
        title_text = f"『{target_player[0]}』の成績 (直近 {target_count} ゲーム)"

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])
    fig.suptitle(title_text, fontsize = 12)

    # 累積推移
    point_ax = fig.add_subplot(grid[0])
    point_ax.set_ylabel("ポイント")
    point_ax.set_xlim(-1, len(game_time))
    point_ax.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    point_ax.plot(game_time, stacked_point, marker = "o", markersize = 3, label = f"累積ポイント({str(total_point)}pt)".replace("-", "▲"))
    point_ax.bar(game_time, game_point, color = "dodgerblue", label = f"獲得ポイント")
    point_ax.tick_params(axis = "x", labelsize = 0, labelcolor = "white") # 背景色と同じにして見えなくする
    point_ax.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0)

    ticks = point_ax.get_yticks()
    point_ax.set_yticks(ticks[1:-1])
    new_ticks = [str(int(i)).replace("-", "▲") for i in ticks]
    point_ax.set_yticklabels(new_ticks[1:-1])

    # 順位分布
    rank_ax = fig.add_subplot(grid[1], sharex = point_ax)
    rank_ax.invert_yaxis()
    rank_ax.set_ylabel("順位")
    rank_ax.set_xlabel(_xlabel)
    rank_ax.set_xlim(-1, len(game_time))
    rank_ax.set_ylim(4.2, 0.8)
    rank_ax.hlines(y = 2.5, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    rank_ax.plot(game_time, game_rank, marker = "o", markersize = 3, label = f"獲得順位")
    rank_ax.plot(game_time, rank_avg, marker = "o", markersize = 3, label = f"平均順位({rank_avg[-1]})")
    rank_ax.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0)

    plt.setp(rank_ax.get_xticklabels(), rotation = rotation, ha = position)
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "graph.png"))

    return(len(game_time))
