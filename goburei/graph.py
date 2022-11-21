import re
import os
import datetime

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.font_manager import FontProperties

from function import global_value as g
from function import common
from function import message
from function import slack_api
from goburei import search
from goburei import member


# イベントAPI
@g.app.message(re.compile(r"^御無礼グラフ"))
def handle_goburei_graph_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(r"^御無礼グラフ$", command):
        return

    slackpost(client, context.channel_id, argument)


def slackpost(client, channel, argument):
    """
    ポイント推移グラフをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、集計期間などが指定される
    """

    starttime = False
    endtime = False
    target_player = []
    target_day = []
    msg = message.invalid_argument()

    for keyword in argument:
        if re.match(r"^(今月|先月|先々月|全部)$", keyword):
            starttime, endtime = common.scope_coverage(keyword)
        if re.match(r"^[0-9]{8}$", common.ZEN2HAN(keyword)):
            target_day.append(common.ZEN2HAN(keyword))
        if member.ExsistPlayer(keyword):
            target_player.append(member.ExsistPlayer(keyword))

    if len(target_day) == 0 and not (starttime or endtime):
        starttime, endtime = common.scope_coverage()
    if len(target_day) == 1:
        starttime, endtime = common.scope_coverage(target_day[0])
    if len(target_day) >= 2:
        starttime, dummy = common.scope_coverage(min(target_day))
        dummy, endtime = common.scope_coverage(max(target_day))
    if not (starttime or endtime) and target_player:
        starttime, endtime = common.scope_coverage()

    if starttime or endtime:
        if len(target_player) == 1: # 描写対象がひとり → 個人成績
            count = plot_personal(starttime, endtime, target_player)
        else: # 描写対象が複数 → 比較
            count = plot(starttime, endtime, target_player)
        file = os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png")
        if count <= 0:
            msg = f"{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')} に御無礼はありません。"
            slack_api.post_message(client, channel, msg)
        else:
            slack_api.post_fileupload(client, channel, "御無礼グラフ", file)
    else:
        slack_api.post_message(client, channel, msg)


def plot(starttime, endtime, target_player, name_replace = True, guest_skip = True):
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

    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default True
        2ゲスト戦の除外

    Returns
    -------
    int : int
        グラフにプロットしたゲーム数
    """

    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)

    ### データ抽出 ###
    gdata = {}
    game_time = []
    player_list = []

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            if target_player: # 指定プレーヤーのみ抽出
                for seki in ("東家", "南家", "西家", "北家"):
                    if results[i][seki]["name"] in target_player:
                        if not results[i]["日付"] in gdata:
                            gdata[results[i]["日付"]] = []
                            game_time.append(results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"))
                        gdata[results[i]["日付"]].append((results[i][seki]["name"], results[i][seki]["point"]))
                        if not results[i][seki]["name"] in player_list:
                            player_list.append(results[i][seki]["name"])
            else: # 全員分
                gdata[results[i]["日付"]] = []
                game_time.append(results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"))
                for seki in ("東家", "南家", "西家", "北家"):
                    gdata[results[i]["日付"]].append((results[i][seki]["name"], results[i][seki]["point"]))
                    if not results[i][seki]["name"] in player_list:
                        player_list.append(results[i][seki]["name"])

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

    plt.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    plt.title(
        f"ポイント推移 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})",
        fontproperties = fp,
        fontsize = 12,
    )
    plt.ylabel("累計ポイント", fontproperties = fp)

    for name, total in ranking:
        label = f"{name} ({str(total)})".replace("-", "▲")
        plt.plot(game_time, stacked_point[name], marker = "o", markersize = 3, label = label)
    plt.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0, prop = fp)
    plt.tight_layout()
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png"))

    return(len(gdata))


def plot_personal(starttime, endtime, target_player, name_replace = True, guest_skip = False):
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

    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default False
        2ゲスト戦の除外

    Returns
    -------
    int : int
        グラフにプロットしたゲーム数
    """

    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)

    ### データ抽出 ###
    game_point = []
    game_rank = []
    game_time = []

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            for seki in ("東家", "南家", "西家", "北家"):
                if results[i][seki]["name"] in target_player:
                    game_time.append(results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"))
                    game_point.append(results[i][seki]["point"])
                    game_rank.append(results[i][seki]["rank"])

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

    grid = gridspec.GridSpec(nrows = 2, ncols = 1, height_ratios = [3, 1])

    fig.suptitle(
        f"『{target_player[0]}』の成績 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})",
        fontproperties = fp,
        fontsize = 12,
    )

    # 累積推移
    point_ax = fig.add_subplot(grid[0])
    point_ax.set_ylabel("ポイント", fontproperties = fp)
    point_ax.set_xlim(-1, len(game_time))
    point_ax.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    point_ax.plot(game_time, stacked_point, marker = "o", markersize = 3, label = f"累計ポイント({str(total_point)})".replace("-", "▲"))
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
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png"))

    return(len(game_time))
