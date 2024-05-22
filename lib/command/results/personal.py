import textwrap

import pandas as pd

import lib.function as f
import lib.database as d
from lib.function import global_value as g


def aggregation(argument, command_option):
    """
    個人成績を集計して返す

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

    ### データ収集 ###
    _, first_game, last_game = d.aggregate.game_count(argument, command_option)
    result_df = d.aggregate.personal_results(argument, command_option)
    record_df = d.aggregate.personal_record(argument, command_option)
    result_df = pd.merge(result_df, record_df, on = ["プレイヤー名", "表示名"])
    data = result_df.to_dict(orient = "records")[0]

    ### 表示内容 ###
    badge_degree = f.common.badge_degree(data["ゲーム数"])
    badge_status = f.common.badge_status(data["ゲーム数"], data["win"])

    msg1 = f"""
        *【個人成績】*
        \tプレイヤー名： {data["表示名"]} {badge_degree}
        \t集計範囲： {first_game} ～ {last_game}
        \t対戦数：{data["ゲーム数"]} 戦 ({data["win"]} 勝 {data["lose"]} 敗 {data["draw"]} 分)  {badge_status}
    """.replace("-", "/")

    msg2 = {}

    if data["ゲーム数"] == 0:
        return(textwrap.dedent(msg1).strip(), msg2)

    msg1 += f"""
        \t累積ポイント： {data['累積ポイント']:+.1f}
        \t平均ポイント： {data['平均ポイント']:+.1f}
        \t平均順位： {data['平均順位']:1.2f}
        \t1位： {data['1位']:2} 回 ({data['1位率']:.2f}%)
        \t2位： {data['2位']:2} 回 ({data['2位率']:.2f}%)
        \t3位： {data['3位']:2} 回 ({data['3位率']:.2f}%)
        \t4位： {data['4位']:2} 回 ({data['4位率']:.2f}%)
        \tトビ： {data['トビ']:2} 回 ({data['トビ率']:.2f}%)
        \t役満： {data['役満和了']:2} 回 ({data['役満和了率']:.2f}%)
        \t{f.message.remarks(command_option)}
    """.replace("-", "▲")

    # --- 座席データ
    msg2["座席"] = textwrap.dedent(f"""
        *【座席データ】*
        \t# 席：順位分布(平順) / トビ / 役満 #
        \t東家： {data['東家-1位']}-{data['東家-2位']}-{data['東家-3位']}-{data['東家-4位']} ({data['東家-平均順位']:1.2f}) / {data['東家-トビ']} / {data['東家-役満和了']}
        \t南家： {data['南家-1位']}-{data['南家-2位']}-{data['南家-3位']}-{data['南家-4位']} ({data['南家-平均順位']:1.2f}) / {data['南家-トビ']} / {data['南家-役満和了']}
        \t西家： {data['西家-1位']}-{data['西家-2位']}-{data['西家-3位']}-{data['西家-4位']} ({data['西家-平均順位']:1.2f}) / {data['西家-トビ']} / {data['西家-役満和了']}
        \t北家： {data['北家-1位']}-{data['北家-2位']}-{data['北家-3位']}-{data['北家-4位']} ({data['北家-平均順位']:1.2f}) / {data['北家-トビ']} / {data['北家-役満和了']}
    """)

    # --- 記録
    msg2["記録"] = textwrap.dedent(f"""
        *【ベストレコード】*
        \t連続トップ： {data['連続トップ']} 連続
        \t連続連対： {data['連続連対']} 連続
        \t連続ラス回避： {data['連続ラス回避']} 連続
        \t最大素点： {data['最大素点'] * 100} 点
        \t最大獲得ポイント： {data['最大獲得ポイント']} pt

        *【ワーストレコード】*
        \t連続ラス： {data['連続ラス']} 連続
        \t連続逆連対： {data['連続逆連対']} 連続
        \t連続トップなし： {data['連続トップなし']} 連続
        \t最小素点： {data['最小素点'] * 100} 点
        \t最小獲得ポイント： {data['最小獲得ポイント']} pt
    """).replace("-", "▲").replace("： 1 連続", "： ----")

    # --- 戦績
    if command_option["game_results"]:
        df = d.aggregate.game_details(argument, command_option)
        if command_option["verbose"]:
            msg2["戦績"] = f"*【戦績】*\n"
            for p in df["playtime"].unique():
                seat1 = df.query("playtime == @p and seat == 1").to_dict(orient = "records")[0]
                seat2 = df.query("playtime == @p and seat == 2").to_dict(orient = "records")[0]
                seat3 = df.query("playtime == @p and seat == 3").to_dict(orient = "records")[0]
                seat4 = df.query("playtime == @p and seat == 4").to_dict(orient = "records")[0]
                guest_count = df.query("playtime == @p and guest == 1").sum()["guest"]
                msg2["戦績"] += textwrap.dedent(f"""
                    {p.replace("-", "/")} {"(2ゲスト戦)" if guest_count >= 2 else ""}
                    \t東家： {seat1["表示名"]} {seat1["rank"]}位 {seat1["rpoint"] * 100:>7}点 ({seat1["point"]:>+5.1f}pt) {seat1["grandslam"]}
                    \t南家： {seat2["表示名"]} {seat2["rank"]}位 {seat2["rpoint"] * 100:>7}点 ({seat2["point"]:>+5.1f}pt) {seat2["grandslam"]}
                    \t西家： {seat3["表示名"]} {seat3["rank"]}位 {seat3["rpoint"] * 100:>7}点 ({seat3["point"]:>+5.1f}pt) {seat3["grandslam"]}
                    \t北家： {seat4["表示名"]} {seat4["rank"]}位 {seat4["rpoint"] * 100:>7}点 ({seat4["point"]:>+5.1f}pt) {seat4["grandslam"]}
                """).replace("-", "▲").strip() + "\n"
        else:
            msg2["戦績"] = f"*【戦績】* （{g.guest_mark.strip()}：2ゲスト戦）\n"
            x = df.query("プレイヤー名 == @data['プレイヤー名']")
            for _, v in x.iterrows():
                guest_count = df.query("playtime == @v['playtime'] and guest == 1").sum()["guest"]
                msg2["戦績"] += "{} {}\t{}位 {:>7}点 ({:>+5.1f}pt) {}\n".format(
                    v["playtime"].replace("-", "/"),
                    g.guest_mark.strip() if guest_count >= 2 else "",
                    v["rank"], v["rpoint"] * 100, v["point"], v["grandslam"],
                ).replace("-", "▲")

    # --- 対戦結果
    print(command_option)
    if command_option["versus_matrix"]:
        df = d.aggregate.versus_matrix(argument, command_option)
        msg2["対戦"] = "\n*【対戦結果】*\n"
        for _, r in df.iterrows():
            msg2["対戦"] += f"\t{r['vs_表示名']}：{r['game']} 戦 {r['win']} 勝 {r['lose']} 敗 ({r['win%']:.2f}%)\n"

    return(textwrap.dedent(msg1), msg2)
