import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib import gridspec

import lib.function as f
import lib.command as c
import lib.command.graph._query as query
from lib.function import global_value as g


mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    """
    個人成績のグラフを生成する

    Parameters
    ----------
    starttime : date
        集計開始日時

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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = query.select_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    target_count = ret["target_count"]
    starttime = ret["starttime"]
    endtime = ret["endtime"]

    # --- データ収集
    playtime = []
    point = []
    point_sum = []
    point_avg = []
    rank = []
    rank_avg = []
    for row in rows.fetchall():
        target_player = c.NameReplace(row["name"], command_option, add_mark = True)
        playtime.append(row["playtime"])
        point.append(row["point"])
        point_sum.append(row["point_sum"])
        point_avg.append(row["point_avg"])
        rank.append(row["rank"])
        rank_avg.append(row["rank_avg"])
        g.logging.trace(f"{dict(row)}")
    g.logging.info(f"return record: {len(playtime)}")

    game_count = len(playtime)

    if game_count == 0:
        return(game_count, f.message.no_hits(argument, command_option))

    ### グラフ生成 ###
    save_file = os.path.join(os.path.realpath(os.path.curdir), "graph.png")
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

    if game_count > 10:
        rotation = 60
    if game_count > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(game_count / 5), 8))
        rotation = 90
        position = "center"
    if game_count == 1:
        rotation = 0
        position = "center"

    _xlabel = f"ゲーム終了日時（{game_count} ゲーム）"
    if target_count == 0:
        title_text = f"『{target_player}』の成績 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
    else:
        title_text = f"『{target_player}』の成績 (直近 {target_count} ゲーム)"

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])
    fig.suptitle(title_text, fontsize = 12)

    # 累積推移
    point_ax = fig.add_subplot(grid[0])
    point_ax.set_ylabel("ポイント")
    point_ax.set_xlim(-1, game_count)
    point_ax.hlines(y = 0, xmin = -1, xmax = game_count, linewidth = 0.5, linestyles="dashed", color = "grey")
    point_ax.plot(playtime, point_sum, marker = "o", markersize = 3, label = f"累積ポイント({str(point_sum[-1])}pt)".replace("-", "▲"))
    point_ax.plot(playtime, point_avg, marker = "o", markersize = 3, label = f"平均ポイント({str(point_avg[-1])}pt)".replace("-", "▲"))
    point_ax.bar(playtime, point, color = "dodgerblue", label = f"獲得ポイント")
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
    rank_ax.set_xlim(-1, game_count)
    rank_ax.set_ylim(4.2, 0.8)
    rank_ax.hlines(y = 2.5, xmin = -1, xmax = game_count, linewidth = 0.5, linestyles="dashed", color = "grey")
    rank_ax.plot(playtime, rank, marker = "o", markersize = 3, label = f"獲得順位")
    rank_ax.plot(playtime, rank_avg, marker = "o", markersize = 3, label = f"平均順位({rank_avg[-1]})")
    rank_ax.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0)

    plt.setp(rank_ax.get_xticklabels(), rotation = rotation, ha = position)
    fig.tight_layout()
    fig.savefig(save_file)

    return(game_count, save_file)
