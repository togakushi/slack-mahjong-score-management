import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def aggregation(starttime, endtime, target_player, target_count, command_option):
    """
    直接対戦結果を集計して返す

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー

    target_count: int
        集計するゲーム数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        slackにpostするデータ

    msg2 : dict
        slackにpostするデータ(スレッドに返す)
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]
    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    results = f.search.game_select(starttime, endtime, target_player, target_count, command_option)
    target_player = [c.NameReplace(name, command_option, add_mark = True) for name in target_player] # ゲストマーク付きリストに更新
    g.logging.info(f"target_player(update):  {target_player}")

    msg2 = {}
    msg1 = "*【直接対戦結果】*\n"
    msg1 += f"\tプレイヤー名： {target_player[0]}\n"

    if command_option["all_player"]:
        vs_list = list(set(g.member_list.values()))
        vs_list.remove(target_player[0]) # 自分を除外
        msg1 += f"\t対戦相手：全員\n"
    else:
        vs_list = target_player[1:]
        msg1 += f"\t対戦相手：{', '.join(vs_list)}\n"

    if results.keys():
        msg1 += "\t集計範囲：{} ～ {}\n".format(
            results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M'),
            results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M'),
        )
        msg1 += f.remarks(command_option)
    else:
        msg1 += "\t集計範囲：{} ～ {}\n".format(
            starttime.strftime('%Y/%m/%d %H:%M'),
            endtime.strftime('%Y/%m/%d %H:%M'),
        )
        msg1 += f.remarks(command_option)
        msg2[""] = "対戦記録が見つかりませんでした。\n"

        return(msg1, msg2)

    padding = c.CountPadding(vs_list)
    g.logging.info(f"vs_list: {vs_list} padding: {padding}")

    for versus_player in vs_list:
        # 同卓したゲームの抽出
        vs_game = []
        for i in results.keys():
            vs_flag = [False, False]
            for wind in g.wind[0:4]:
                if target_player[0] == results[i][wind]["name"]:
                    vs_flag[0] = True
                if versus_player == results[i][wind]["name"]:
                    vs_flag[1] = True
            if vs_flag[0] and vs_flag[1]:
                vs_game.append(i)

        ### 対戦結果集計 ###
        win = 0 # 勝ち越し数
        my_aggr = { # 自分の集計結果
            "r_total": 0, # 素点合計
            "total": 0, # ポイント合計
            "rank": [0, 0, 0, 0],
        }
        vs_aggr = { # 相手の集計結果
            "r_total": 0, # 素点合計
            "total": 0, # ポイント合計
            "rank": [0, 0, 0, 0],
        }

        if target_player[0] == versus_player:
            continue

        msg2[versus_player] = "[ {} vs {} ]\n".format(target_player[0], versus_player)

        for i in vs_game:
            for wind in g.wind[0:4]:
                if target_player[0] == results[i][wind]["name"]:
                    r_m = results[i][wind]
                    my_aggr["r_total"] += eval(str(results[i][wind]["rpoint"])) * 100
                    my_aggr["total"] += results[i][wind]["point"]
                    my_aggr["rank"][results[i][wind]["rank"] -1] += 1
                if versus_player == results[i][wind]["name"]:
                    r_v = results[i][wind]
                    vs_aggr["r_total"] += eval(str(results[i][wind]["rpoint"])) * 100
                    vs_aggr["total"] += results[i][wind]["point"]
                    vs_aggr["rank"][results[i][wind]["rank"] -1] += 1

            if r_m["rank"] < r_v["rank"]:
                win += 1

        ### 集計結果出力 ###
        if len(vs_game) == 0:
            msg2.pop(versus_player)
        else:
            msg2[versus_player] += "対戦数： {} 戦 {} 勝 {} 敗\n".format(len(vs_game), win, len(vs_game) - win)
            msg2[versus_player] += "平均素点差： {:+.1f}点\n".format(
                (my_aggr["r_total"] - vs_aggr["r_total"]) / len(vs_game)
            ).replace("-", "▲")
            msg2[versus_player] += "獲得ポイント合計(自分)： {:+.1f}pt\n".format(
                my_aggr["total"]
            ).replace("-", "▲")
            msg2[versus_player] += "獲得ポイント合計(相手)： {:+.1f}pt\n".format(
                vs_aggr["total"]
            ).replace("-", "▲")
            msg2[versus_player] += "順位分布(自分)： {}-{}-{}-{} ({:1.2f})\n".format(
                my_aggr["rank"][0], my_aggr["rank"][1], my_aggr["rank"][2], my_aggr["rank"][3],
                sum([my_aggr["rank"][i] * (i + 1) for i in range(4)]) / sum(my_aggr["rank"]),
            )
            msg2[versus_player] += "順位分布(相手)： {}-{}-{}-{} ({:1.2f})\n".format(
                vs_aggr["rank"][0], vs_aggr["rank"][1], vs_aggr["rank"][2], vs_aggr["rank"][3],
                sum([vs_aggr["rank"][i] * (i + 1) for i in range(4)]) / sum(vs_aggr["rank"]),
            )
            if command_option["game_results"]:
                msg2[versus_player] += "\n[ゲーム結果]\n"
                for i in vs_game:
                    msg2[versus_player] += results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S\n")
                    for wind in g.wind[0:4]:
                        tmp_msg = "\t{}： {}{} / {}位 {:>5}00点 ({}pt)\n".format(
                            wind, results[i][wind]["name"],
                            " " * (padding - f.translation.len_count(results[i][wind]["name"])),
                            results[i][wind]["rank"],
                            eval(str(results[i][wind]["rpoint"])),
                            results[i][wind]["point"],
                        ).replace("-", "▲")

                        if command_option["verbose"]:
                            msg2[versus_player] += tmp_msg
                        elif results[i][wind]["name"] in (target_player[0], versus_player):
                            msg2[versus_player] += tmp_msg

    if not msg2:
        msg2[""] = "直接対戦はありません。\n"

    return(msg1.strip(), msg2)
