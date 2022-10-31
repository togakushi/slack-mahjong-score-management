import re
import os
import datetime

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from function import global_value as g
from function import common
from function import error
from function import slack_api
from goburei import search
from goburei import member


# イベントAPI
@g.app.message(re.compile(r"^御無礼グラフ"))
def handle_goburei_graph_evnts(client, context, body):
    v = body["event"]["text"].split()

    if not re.match(r"^御無礼グラフ$", v[0]):
        return

    slackpost(client, context.channel_id, v[1:])


def slackpost(client, channel, keyword):
    """
    ポイント推移グラフをslackにポストする

    Parameters
    ----------
    client : obj

    channel : str
        ポスト先のチャンネルID or ユーザーID

    keyword : list
        解析対象のプレイヤー、集計期間
    """

    starttime = False
    endtime = False
    target_player = []
    msg = error.message()

    for i in keyword:
        if re.match(r"^(今月|先月|先々月|全部)$", i):
            starttime, endtime = common.scope_coverage(i)
        if re.match(r"^[0-9]{8}$", i):
            starttime, endtime = common.scope_coverage(i)
        if member.ExsistPlayer(i):
            target_player.append(member.ExsistPlayer(i))

    if len(keyword) == 0:
        starttime, endtime = common.scope_coverage()

    if not (starttime or endtime) and target_player:
        starttime, endtime = common.scope_coverage()

    if starttime or endtime:
        count = plot(starttime, endtime, target_player)
        file = os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png")
        if count <= 0:
            msg = f"{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')} に御無礼はありません。"
            slack_api.post_message(client, channel, msg)
        else:
            slack_api.post_fileupload(client, channel, "御無礼グラフ", file)
    else:
        slack_api.post_message(client, channel, msg)


def plot(starttime, endtime, target_player, name_replace = True, guest_skip = True): # 御無礼グラフ
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
    gdata = {}
    game_time = []
    player_list = []

    ### データ抽出 ###
    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            if target_player: # 特定プレーヤーのみ抽出
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
    plt.xticks(rotation = 45)

    # サイズ、表記調整
    if len(game_time) > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(len(game_time) / 5), 8))
        plt.xlim(-1, len(game_time))
    if len(game_time) > 6:
        plt.xticks(rotation = 90)
    if len(game_time) == 1:
        plt.xticks(rotation = 0)

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
