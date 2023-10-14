import os
import re

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.font_manager import FontProperties

import lib.command as c
import lib.function as f
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)

commandword = g.config["graph"].get("commandword", "麻雀グラフ")
g.logging.info(f"[import] graph {commandword}")


# イベントAPI
@g.app.message(re.compile(rf"^{commandword}"))
def handle_graph_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(rf"^{commandword}$", command):
        return

    command_option = f.configure.command_option_initialization("graph")
    g.logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


def slackpost(client, channel, argument, command_option):
    """
    ポイント推移グラフをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される

    command_option : dict
        コマンドオプション
    """

    msg = f.message.invalid_argument()
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    if starttime or endtime:
        if len(target_player) == 1: # 描写対象がひとり → 個人成績
            command_option["guest_skip"] = False
            count = plot_personal(starttime, endtime, target_player, target_count, command_option)
        else: # 描写対象が複数 → 比較
            count = plot(starttime, endtime, target_player, target_count, command_option)
        file = os.path.join(os.path.realpath(os.path.curdir), "graph.png")
        if count <= 0:
            f.slack_api.post_message(client, channel, f.message.no_hits(starttime, endtime))
        else:
            f.slack_api.post_fileupload(client, channel, "成績グラフ", file)
    else:
        f.slack_api.post_message(client, channel, msg)


def plot(starttime, endtime, target_player, target_count, command_option):
    """
    ポイント推移グラフを生成する

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

    g.logging.info(f"[graph.plot] {starttime} {endtime} {target_player} {target_count} {command_option}")
    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

    ### データ抽出 ###
    gdata = {}
    game_time = []
    player_list = []

    for i in results.keys():
        pdate = results[i]["日付"]
        if target_player: # 指定プレーヤーのみ抽出
            for wind in g.wind[0:4]:
                pname = results[i][wind]["name"]
                if pname in target_player:
                    if not pdate in gdata:
                        gdata[pdate] = []
                        game_time.append(pdate.strftime("%Y/%m/%d %H:%M:%S"))
                    gdata[pdate].append((pname, results[i][wind]["point"]))
                    if not pname in player_list:
                        player_list.append(pname)
        else: # 全員分
            gdata[pdate] = []
            game_time.append(pdate.strftime("%Y/%m/%d %H:%M:%S"))
            for wind in g.wind[0:4]:
                pname = results[i][wind]["name"]
                if not command_option["guest_skip"] and pname == g.guest_name:
                    continue
                gdata[pdate].append((pname, results[i][wind]["point"]))
                if not pname in player_list:
                    player_list.append(pname)

    if len(game_time) == 0:
        return(len(game_time))

    ### 集計 ###
    stacked_point = {}
    for name in player_list:
        stacked_point[name] = []
        total_point = 0
        for i in gdata:
            point = 0
            for n, p in gdata[i]:
                if name == n:
                    point = p
            total_point = round(total_point + point, 2)
            stacked_point[name].append(total_point)
    # sort
    rank = {}
    for name in player_list:
        rank[name] = stacked_point[name][-1]
    ranking = sorted(rank.items(), key=lambda x:x[1], reverse=True)

    ### グラフ生成 ###
    fp = FontProperties(
        fname = os.path.join(os.path.realpath(os.path.curdir), "ipaexg.ttf"),
        size = 9,
    )

    fig = plt.figure()
    plt.style.use("ggplot")
    plt.xticks(rotation = 45, ha = "right")

    # サイズ、表記調整
    if len(game_time) > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(len(game_time) / 5), 8))
        plt.xlim(-1, len(game_time))
    if len(game_time) > 10:
        plt.xticks(rotation = 90, ha = "center")
    if len(game_time) == 1:
        plt.xticks(rotation = 0, ha = "center")

    if target_count == 0:
        title_text = f"ポイント推移 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
    else:
        title_text = f"ポイント推移 (直近 {target_count} 戦)"

    plt.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    plt.title(title_text, fontproperties = fp, fontsize = 12)
    plt.ylabel("累積ポイント", fontproperties = fp)

    for name, total in ranking:
        #print("debug:", name, len(game_time), len(stacked_point[name]))
        label = f"{name} ({str(total)})".replace("-", "▲")
        plt.plot(game_time, stacked_point[name], marker = "o", markersize = 3, label = label)
    plt.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0, prop = fp)

    # Y軸修正
    ylocs, ylabs = plt.yticks()
    new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
    plt.yticks(ylocs[1:-1], new_ylabs[1:-1])

    plt.tight_layout()
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "graph.png"))

    return(len(gdata))


def plot_personal(starttime, endtime, target_player, target_count, command_option):
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

    g.logging.info(f"[graph.plot_personal] {starttime} {endtime} {target_player} {target_count} {command_option}")
    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

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
    fp = FontProperties(
        fname = os.path.join(os.path.realpath(os.path.curdir), "ipaexg.ttf"),
        size = 9,
    )

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
    if target_count == 0:
        title_text = f"『{target_player[0]}』の成績 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
    else:
        title_text = f"『{target_player[0]}』の成績 (直近 {target_count} 戦)"

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])
    fig.suptitle(title_text, fontproperties = fp, fontsize = 12)

    # 累積推移
    point_ax = fig.add_subplot(grid[0])
    point_ax.set_ylabel("ポイント", fontproperties = fp)
    point_ax.set_xlim(-1, len(game_time))
    point_ax.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    point_ax.plot(game_time, stacked_point, marker = "o", markersize = 3, label = f"累積ポイント({str(total_point)})".replace("-", "▲"))
    point_ax.bar(game_time, game_point, color = "dodgerblue", label = f"獲得ポイント")
    point_ax.tick_params(axis = "x", labelsize = 0, labelcolor = "white") # 背景色と同じにして見えなくする
    point_ax.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0, prop = fp)

    # 順位分布
    rank_ax = fig.add_subplot(grid[1], sharex = point_ax)
    rank_ax.invert_yaxis()
    rank_ax.set_ylabel("順位", fontproperties = fp)
    rank_ax.set_xlim(-1, len(game_time))
    rank_ax.set_ylim(4.2, 0.8)
    rank_ax.hlines(y = 2.5, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    rank_ax.plot(game_time, game_rank, marker = "o", markersize = 3, label = f"獲得順位")
    rank_ax.plot(game_time, rank_avg, marker = "o", markersize = 3, label = f"平均順位({rank_avg[-1]})")
    rank_ax.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0, prop = fp)

    plt.setp(rank_ax.get_xticklabels(), rotation = rotation, ha = position)
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "graph.png"))

    return(len(game_time))
