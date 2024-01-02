import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.command as c
import lib.command.graph._query as query
from lib.function import global_value as g


mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    """
    ポイント推移/順位変動グラフを生成する

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
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    command_option["fourfold"] = True # 直近Nは4倍する(縦持ちなので4人分)
    ret = query.select_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    target_count = ret["target_count"]
    starttime = ret["starttime"]
    endtime = ret["endtime"]

    # --- データ収集
    tmp_results = {}
    playtime = []
    for row in rows.fetchall():
        if not row["name"] in tmp_results:
            tmp_results[row["name"]] = {
                "playtime": [],
                "point_sum": [],
                "interim_rank": [],
                "count": 0,
            }
        playtime.append(row["playtime"])
        tmp_results[row["name"]]["playtime"].append(row["playtime"])
        tmp_results[row["name"]]["point_sum"].append(row["point_sum"])
        tmp_results[row["name"]]["count"] = row["count"]
        g.logging.trace(f"{row['name']}: {tmp_results[row['name']]}")
    g.logging.info(f"return record: {len(tmp_results)}")

    playtime = list(set(playtime))
    playtime.sort()
    game_count = len(playtime)

    # 累積ポイント推移
    results = {}
    for name in tmp_results.keys():
        results[name] = {
            "playtime": [],
            "point_sum": [],
            "interim_rank": [],
            "count": tmp_results[name]["count"],
        }
        point = None
        for i in range(game_count):
            if playtime[i] in tmp_results[name]["playtime"]:
                position = tmp_results[name]["playtime"].index(playtime[i])
                point = tmp_results[name]["point_sum"][position]
            results[name]["playtime"].append(playtime[i])
            results[name]["point_sum"].append(point)

    # 順位推移
    for i in range(game_count):
        ranking = list(set([results[x]["point_sum"][i] for x in results.keys()]))
        if None in ranking:
            ranking.remove(None)
        ranking.sort(reverse = True)

        for name in results.keys(): # Todo: 同点のとき重なる
            if results[name]["point_sum"][i]:
                results[name]["interim_rank"].append(list(ranking).index(results[name]["point_sum"][i]) + 1)
            else:
                results[name]["interim_rank"].append(None)

    # 最終順位順に並べ替え
    ranking_point = {}
    ranking_rank = {}
    for name in results.keys():
        ranking_point[name] = results[name]["point_sum"][-1]
        ranking_rank[name] = results[name]["interim_rank"][-1]

    ranking_point = sorted(ranking_point.items(), key = lambda x:x[1], reverse = True)
    ranking_rank = sorted(ranking_rank.items(), key = lambda x:x[1])

    ### グラフ生成 ###
    # --- グラフフォント設定
    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    fig = plt.figure()
    plt.style.use("ggplot")
    plt.xticks(rotation = 45, ha = "right")

    # サイズ、表記調整
    if game_count > 20:
        fig = plt.figure(figsize = (8 + 0.5 * int(game_count / 5), 8))
        plt.xlim(-1, game_count)
    if game_count > 10:
        plt.xticks(rotation = 90, ha = "center")
    if game_count == 1:
        plt.xticks(rotation = 0, ha = "center")

    # タイトルと軸ラベル
    _xlabel = f"ゲーム終了日時（{game_count} ゲーム）"
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

    plt.hlines(y = 0, xmin = -1, xmax = game_count, linewidth = 0.5, linestyles="dashed", color = "grey")
    plt.title(title_text, fontsize = 12)
    plt.ylabel(_ylabel)
    plt.xlabel(_xlabel)

    if command_option["order"]:
        for name, _ in ranking_rank:
            label = "{}位：{} {}pt / {}G)".format(
                str(results[name]["interim_rank"][-1]),
                c.NameReplace(name, command_option, add_mark = True),
                str(results[name]["point_sum"][-1]),
                str(results[name]["count"]),
            ).replace("-", "▲")
            plt.plot(playtime, results[name]["interim_rank"], marker = "o", markersize = 3, label = label)
        if game_count < 10:
            plt.yticks([i for i in range(len(results) + 2)])
        else:
            # Y軸の目盛り設定(多めにリストを作って描写範囲まで削る)
            yl = [i for i in range(-(int(len(results) / 20) + 1), int(len(results) * 1.5), int(len(results) / 20) + 2)]
            while yl[-2] > len(results):
                yl.pop()
            plt.yticks(yl)
        plt.ylim(0.2, len(results) + 0.8)
        plt.gca().invert_yaxis()
    else:
        for name, _ in ranking_point:
            label = "{} ({}pt / {}G)".format(
                c.NameReplace(name, command_option, add_mark = True),
                str(results[name]["point_sum"][-1]),
                str(results[name]["count"]),
            ).replace("-", "▲")
            plt.plot(playtime, results[name]["point_sum"], marker = "o", markersize = 3, label = label)

    # 凡例
    plt.legend(
        bbox_to_anchor = (1.03, 1),
        loc = "upper left",
        borderaxespad = 0,
        ncol = int(len(results.keys()) / 30 + 1),
    )

    # Y軸修正
    ylocs, ylabs = plt.yticks()
    new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
    plt.yticks(ylocs[1:-1], new_ylabs[1:-1])

    plt.tight_layout()
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "graph.png"))

    return(game_count)
