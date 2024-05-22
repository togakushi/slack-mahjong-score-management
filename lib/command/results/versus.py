import textwrap

import lib.command as c
import lib.function as f
import lib.database as d
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

    # --- データ収集
    param = d.common.placeholder_params(argument, command_option)
    df = d.aggregate.versus_matrix(argument, command_option)
    df_game = d.aggregate.game_details(argument, command_option)

    # --- ヘッダ情報
    my_name = param["player_name"]
    if command_option["all_player"]:
        vs = "全員"
        vs_list = set(g.member_list.values())
    else:
        vs = ",".join(param["competition_list"].values())
        vs_list = list(df_game["プレイヤー名"].unique())

    msg1 = textwrap.dedent(f"""
        *【直接対戦結果】*
        \tプレイヤー名：{c.member.NameReplace(my_name, command_option, add_mark = True)}
        \t対戦相手：{vs}
        \t検索範囲：{param["starttime"].strftime("%Y/%m/%d %H:%M")} ～ {param["endtime"].strftime("%Y/%m/%d %H:%M")}
        \t{f.message.remarks(command_option)}
    """).strip() + "\n"

    # --- 表示内容
    msg2 = {}
    if len(df) == 0: # 検索結果なし
        msg2[""] = "対戦記録が見つかりません。\n"

    for vs_name in param["competition_list"].values():
        msg2[vs_name] = {}
        if vs_name in vs_list:
            data = df.query("vs_name == @vs_name")

            if len(data) == 0:
                msg2[vs_name]["info"] = "【{} vs {}】\n\t対戦記録はありません。\n".format(
                    c.member.NameReplace(my_name, command_option, add_mark = True),
                    c.member.NameReplace(vs_name, command_option, add_mark = True),
                )
                continue

            r = data.to_dict(orient = "records")[0]
            msg2[vs_name]["info"] = textwrap.dedent(f"""
                【{r["my_表示名"].strip()} vs {r["vs_表示名"].strip()}】
                \t対戦数： {r["game"]} 戦 {r["win"]} 勝 {r["lose"]} 敗 ({r["win%"]:.2f}%)
                \t平均素点差： {(r["my_rpoint_avg"]-r["vs_rpoint_avg"]) * 100:+.0f} 点
                \t獲得ポイント合計(自分)： {r["my_point_sum"]:+.1f}pt
                \t獲得ポイント合計(相手)： {r["vs_point_sum"]:+.1f}pt
                \t順位分布(自分)： {r["my_1st"]}*{r["my_2nd"]}*{r["my_3rd"]}*{r["my_4th"]} ({r["my_rank_avg"]:1.2f})
                \t順位分布(相手)： {r["vs_1st"]}*{r["vs_2nd"]}*{r["vs_3rd"]}*{r["vs_4th"]} ({r["vs_rank_avg"]:1.2f})
            """).replace("-", "▲").replace("*", "-").strip() + "\n\n"

            # ゲーム結果
            if command_option["game_results"]:
                count = 0
                my_score = df_game.query("プレイヤー名 == @my_name")
                vs_score = df_game.query("プレイヤー名 == @vs_name")
                my_playtime = my_score["playtime"].to_list()
                vs_playtime = vs_score["playtime"].to_list()

                for playtime in set(my_playtime + vs_playtime):
                    if playtime in my_playtime and playtime in vs_playtime:
                        current_game = df_game.query("playtime == @playtime")
                        guest_count = current_game["guest"].sum()
                        if command_option["verbose"]: # 詳細表示
                            s1 = current_game.query("seat == 1").to_dict(orient = "records")[0]
                            s2 = current_game.query("seat == 2").to_dict(orient = "records")[0]
                            s3 = current_game.query("seat == 3").to_dict(orient = "records")[0]
                            s4 = current_game.query("seat == 4").to_dict(orient = "records")[0]
                            msg2[vs_name][count] = textwrap.dedent(f"""
                                {"*【戦績】*" if count == 0 else ""}
                                {playtime.replace("-", "/")} {"(2ゲスト戦)" if guest_count >= 2 else ""}
                                \t東家：{s1["表示名"]} {s1["rank"]}位 {s1["rpoint"] * 100:>7} 点 ({s1["point"]:>+5.1f}pt) {s1["grandslam"]}
                                \t南家：{s2["表示名"]} {s2["rank"]}位 {s2["rpoint"] * 100:>7} 点 ({s2["point"]:>+5.1f}pt) {s2["grandslam"]}
                                \t西家：{s3["表示名"]} {s3["rank"]}位 {s3["rpoint"] * 100:>7} 点 ({s3["point"]:>+5.1f}pt) {s3["grandslam"]}
                                \t北家：{s4["表示名"]} {s4["rank"]}位 {s4["rpoint"] * 100:>7} 点 ({s4["point"]:>+5.1f}pt) {s4["grandslam"]}
                                """).replace("-", "▲").strip() + " \n"
                        else: # 簡易表示
                            a1 = my_score.query("playtime == @playtime").to_dict(orient = "records")[0]
                            a2 = vs_score.query("playtime == @playtime").to_dict(orient = "records")[0]
                            msg2[vs_name][count] = textwrap.dedent(f"""
                                {"*【戦績】*" if count == 0 else ""}
                                {playtime.replace("-", "/")} {"(2ゲスト戦)" if guest_count >= 2 else ""}
                                \t{a1["表示名"]}： {a1["rank"]}位 {a1["rpoint"] * 100:>7} 点 ({a1["point"]:>+5.1f}pt) {a1["grandslam"]}
                                \t{a2["表示名"]}： {a2["rank"]}位 {a2["rpoint"] * 100:>7} 点 ({a2["point"]:>+5.1f}pt) {a2["grandslam"]}
                            """).replace("-", "▲").strip() + " \n"
                        count =+ 1
        else: # 対戦記録なし
            msg2[vs_name]["info"] = "【{} vs {}】\n\t対戦相手が見つかりません。\n".format(
                c.member.NameReplace(my_name, command_option, add_mark = True),
                c.member.NameReplace(vs_name, command_option, add_mark = True),
            )

    return(msg1, msg2)
