import os

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.font_manager import FontProperties

import lib.command as c
import lib.function as f
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(starttime, endtime, target_player, target_count, command_option):
    """
    ポイント推移/順位変動グラフを生成する

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

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    results = f.search.game_select(starttime, endtime, target_player, target_count, command_option)
    target_player = [c.NameReplace(name, command_option, add_mark = True) for name in target_player] # ゲストマーク付きリストに更新
    g.logging.info(f"target_player(update):  {target_player}")

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
    game_count = {}
    for name in player_list:
        stacked_point[name] = []
        game_count[name] = 0
        total_point = 0
        for i in gdata:
            for n, p in gdata[i]:
                if name == n:
                    total_point = round(total_point + p, 2)
                    stacked_point[name].append(total_point)
                    game_count[name] += 1
                    break
            else:
                if stacked_point[name]:
                    stacked_point[name].append(stacked_point[name][-1])
                else:
                    stacked_point[name].append(None)

    # 最終順位
    rank = {}
    for name in player_list:
        rank[name] = stacked_point[name][-1]
    ranking = sorted(rank.items(), key = lambda x:x[1], reverse = True)

    # 中間順位
    interim_rank = {}
    point_data = {}
    count = 0
    for name in player_list:
        interim_rank[name] = []
    for i in gdata:
        point_data[i] = []
        for name in stacked_point.keys(): # 評価用リスト生成(ゲーム内のポイントの降順)
            if stacked_point[name][count]:
                point_data[i].append(stacked_point[name][count])
        point_data[i].sort(reverse = True)

        for name in stacked_point.keys(): # 順位付け
            if stacked_point[name][count]:
                interim_rank[name].append(point_data[i].index(stacked_point[name][count]) + 1)
            else:
                interim_rank[name].append(None)
        count += 1

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

    # タイトルと軸ラベル
    _xlabel = f"ゲーム終了日時（{len(game_time)} ゲーム）"
    if command_option["order"]:
        _ylabel = "順位 (累積ポイント順)"
        if target_count == 0:
            title_text = f"順位変動 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
        else:
            title_text = f"順位変動 (直近 {target_count} ゲーム)"
    else:
        _ylabel = "累積ポイント"
        if target_count == 0:
            title_text = f"ポイント推移 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})"
        else:
            title_text = f"ポイント推移 (直近 {target_count} ゲーム)"

    plt.hlines(y = 0, xmin = -1, xmax = len(game_time), linewidth = 0.5, linestyles="dashed", color = "grey")
    plt.title(title_text, fontproperties = fp, fontsize = 12)
    plt.ylabel(_ylabel, fontproperties = fp)
    plt.xlabel(_xlabel, fontproperties = fp)

    if command_option["order"]:
        p = len(interim_rank)
        for name, total in ranking:
            label = f"{str(interim_rank[name][-1])}位：{name} ({str(total)}p/{str(game_count[name])}G)".replace("-", "▲")
            plt.plot(game_time, interim_rank[name], marker = "o", markersize = 3, label = label)
        if p < 10:
            plt.yticks([i for i in range(p + 2)])
        else:
            # Y軸の目盛り設定(多めにリストを作って描写範囲まで削る)
            yl = [i for i in range(-(int(p / 20) + 1), int(p * 1.5), int(p / 20) + 2)]
            while yl[-2] > p:
                yl.pop()
            plt.yticks(yl)
        plt.ylim(0.2, p + 0.8)
        plt.gca().invert_yaxis()
    else:
        for name, total in ranking:
            label = f"{name} ({str(total)}p/{str(game_count[name])}G)".replace("-", "▲")
            plt.plot(game_time, stacked_point[name], marker = "o", markersize = 3, label = label)

    # 凡例
    plt.legend(
        bbox_to_anchor = (1.03, 1),
        loc = "upper left",
        borderaxespad = 0,
        ncol = int(len(player_list) / 30 + 1),
        prop = fp,
    )

    # Y軸修正
    ylocs, ylabs = plt.yticks()
    new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
    plt.yticks(ylocs[1:-1], new_ylabs[1:-1])

    plt.tight_layout()
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "graph.png"))

    return(len(gdata))
