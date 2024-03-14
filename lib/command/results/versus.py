import sqlite3

import lib.command as c
import lib.function as f
import lib.command.results._query as query
from lib.function import global_value as g


def aggregation(argument, command_option):
    """
    直接対戦結果を集計して返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    # --- データ収集
    ret = query.select_versus_matrix(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    my_name = ret["target_player"][0]
    starttime = ret["starttime"]
    endtime = ret["endtime"]

    results = {}
    for row in rows.fetchall():
        results[row["vs_name"]] = dict(row)
        g.logging.trace(f"{row['vs_name']}: {results[row['vs_name']]}") # type: ignore
    g.logging.info(f"return record: {len(results)}")

    # ヘッダ情報
    msg2 = {}
    msg1 = "*【直接対戦結果】*\n"
    msg1 += f"\tプレイヤー名： {my_name}\n"

    if command_option["all_player"]:
        vs_list = list(results.keys())
        msg1 += f"\t対戦相手：全員\n"
    else:
        vs_list = ret["target_player"][1:]
        if my_name in vs_list:
            vs_list.remove(my_name)
        msg1 += f"\t対戦相手：{', '.join(vs_list)}\n"

    msg1 += "\t検索範囲：{} ～ {}\n".format(
        starttime.strftime("%Y/%m/%d %H:%M"),
        endtime.strftime("%Y/%m/%d %H:%M"),
    )
    msg1 += f.message.remarks(command_option)

    if len(vs_list) == 0:
        msg2[""] = "対戦相手が見つかりませんでした。\n"
        return(msg1, msg2)

    if len(results) == 0:
        msg2[""] = "対戦記録が見つかりませんでした。\n"
        return(msg1, msg2)

    # 表示内容
    padding = c.member.CountPadding(
        [c.member.NameReplace(i, command_option, add_mark = True) for i in vs_list + [my_name]]
    )
    g.logging.info(f"vs_list: {vs_list} padding: {padding}")

    for vs_name in vs_list:
        msg2[vs_name] = "[ {} vs {} ]\n".format(
            c.member.NameReplace(my_name, command_option, add_mark = True),
            c.member.NameReplace(vs_name, command_option, add_mark = True),
        )

        msg2[vs_name] += "対戦数： {} 戦 {} 勝 {} 敗\n".format(
            results[vs_name]["game"],
            results[vs_name]["win"],
            results[vs_name]["game"] - results[vs_name]["win"],
        )

        msg2[vs_name] += "平均素点差： {:+.0f}点\n".format(
            (results[vs_name]["my_rpoint_avg"] - results[vs_name]["vs_rpoint_avg"]) * 100
        ).replace("-", "▲")

        msg2[vs_name] += "獲得ポイント合計(自分)： {:+.1f}pt\n".format(results[vs_name]["my_point_sum"]).replace("-", "▲")
        msg2[vs_name] += "獲得ポイント合計(相手)： {:+.1f}pt\n".format(results[vs_name]["vs_point_sum"]).replace("-", "▲")

        msg2[vs_name] += "順位分布(自分)： {}-{}-{}-{} ({:1.2f})\n".format(
            results[vs_name]["my_1st"],
            results[vs_name]["my_2nd"],
            results[vs_name]["my_3rd"],
            results[vs_name]["my_4th"],
            results[vs_name]["my_rank_avg"],
        )
        msg2[vs_name] += "順位分布(相手)： {}-{}-{}-{} ({:1.2f})\n".format(
            results[vs_name]["vs_1st"],
            results[vs_name]["vs_2nd"],
            results[vs_name]["vs_3rd"],
            results[vs_name]["vs_4th"],
            results[vs_name]["vs_rank_avg"],
        )

        # ゲーム結果
        if command_option["game_results"]:
            msg2[vs_name] += "\n[ゲーム結果]\n"
            ret = query.select_game_vs_results(argument, command_option, my_name, vs_name)
            rows = resultdb.execute(ret["sql"], ret["placeholder"])

            for row in rows.fetchall():
                g.logging.trace(dict(row)) # type: ignore
                tmp_msg_v = "{}{}\n".format(
                    row["playtime"],
                    "\t(2ゲスト戦)" if row["guest_count"] >= 2 else "",
                )
                for wind, pre in [("東家", "p1"), ("南家", "p2"), ("西家", "p3"), ("北家", "p4")]:
                    pname = c.member.NameReplace(row[f"{pre}_name"], command_option, add_mark = True)
                    tmp_msg_v += "\t{}： {}{} / {}位 {:>5}点 ({}pt)\n".format(
                        wind, pname, " " * (padding - f.translation.len_count(pname)),
                        row[f"{pre}_rank"],
                        row[f"{pre}_rpoint"],
                        row[f"{pre}_point"],
                    ).replace("-", "▲")
                    if row[f"{pre}_name"] == my_name:
                        tmp_msg_p = "{}： {}位 {:>5}点 ({}pt){}\n".format(
                            row["playtime"],
                            row[f"{pre}_rank"],
                            row[f"{pre}_rpoint"],
                            row[f"{pre}_point"],
                            g.guest_mark if row["guest_count"] >= 2 else "",
                        ).replace("-", "▲")

                if command_option["verbose"]:
                    msg2[vs_name] += tmp_msg_v
                else:
                    msg2[vs_name] += tmp_msg_p

    resultdb.close()
    return(msg1.strip(), msg2)
