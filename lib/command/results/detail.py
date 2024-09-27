import textwrap

import pandas as pd

import global_value as g
from lib import database as d
from lib import function as f


def aggregation():
    """
    個人/チーム成績を集計して返す

    Returns
    -------
    msg1 : text
        slackにpostするデータ

    msg2 : dict
        slackにpostするデータ(スレッドに返す)
    """

    # 検索動作を合わせる
    g.opt.guest_skip = g.opt.guest_skip2

    # --- データ収集
    game_info = d.aggregate.game_info()
    df_grandslam = d.aggregate.grandslam_count()
    df_regulations = d.aggregate.regulations_count()

    if g.opt.individual:
        item_title = "*【個人成績】*"
        item_name = "プレイヤー名"
    else:
        item_title = "*【チーム成績】*"
        item_name = "チーム名"

    if game_info["game_count"] == 0:
        msg1 = f"""
            {item_title}
            \t{item_name}： {g.prm.player_name} {f.common.badge_degree(0)}
            \t検索範囲： {g.prm.starttime_hms} ～ {g.prm.endtime_hms}
            \t{f.message.remarks().strip()}
            \t対戦数： 0 戦 (0 勝 0 敗 0 分) {f.common.badge_status(0, 0)}
        """
        msg1 = f.message.del_blank_line(msg1)
        return (textwrap.dedent(msg1), {})

    result_df = d.aggregate.game_results()
    record_df = d.aggregate.ranking_record()
    result_df = pd.merge(
        result_df, record_df,
        on=["name", "表示名"],
        suffixes=["", "_x"]
    )
    data = result_df.to_dict(orient="records")[0]

    # --- 表示内容
    badge_degree = f.common.badge_degree(data["ゲーム数"])
    badge_status = f.common.badge_status(data["ゲーム数"], data["win"])

    msg1 = f"""
        {item_title}
        \t{item_name}： {data["表示名"].strip()} {badge_degree}
        \t検索範囲： {g.prm.starttime_hms} ～ {g.prm.endtime_hms}
        \t集計範囲： {game_info['first_game']} ～ {game_info['last_game']}
        \t{f.message.remarks().strip()}
        \t対戦数： {data["ゲーム数"]} 戦 ({data["win"]} 勝 {data["lose"]} 敗 {data["draw"]} 分) {badge_status}
    """
    msg1 = f.message.del_blank_line(msg1)
    msg2 = {}

    # --- 成績データ
    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        msg1 += f"""
            \t
            \t通算ポイント： {data['通算ポイント']:+.1f}pt
            \t平均ポイント： {data['平均ポイント']:+.1f}pt
            \t平均順位： {data['平均順位']:1.2f}
            \t1位： {data['1位']:2} 回 ({data['1位率']:6.2f}%)
            \t2位： {data['2位']:2} 回 ({data['2位率']:6.2f}%)
            \t3位： {data['3位']:2} 回 ({data['3位率']:6.2f}%)
            \t4位： {data['4位']:2} 回 ({data['4位率']:6.2f}%)
            \t役満： {data['役満和了']:2} 回 ({data['役満和了率']:6.2f}%)
        """.replace("-", "▲")
    else:
        msg1 += f"""
            \t
            \t通算ポイント： {data['通算ポイント']:+.1f}pt
            \t平均ポイント： {data['平均ポイント']:+.1f}pt
            \t平均順位： {data['平均順位']:1.2f}
            \t1位： {data['1位']:2} 回 ({data['1位率']:6.2f}%)
            \t2位： {data['2位']:2} 回 ({data['2位率']:6.2f}%)
            \t3位： {data['3位']:2} 回 ({data['3位率']:6.2f}%)
            \t4位： {data['4位']:2} 回 ({data['4位率']:6.2f}%)
            \tトビ： {data['トビ']:2} 回 ({data['トビ率']:6.2f}%)
            \t役満： {data['役満和了']:2} 回 ({data['役満和了率']:6.2f}%)
        """.replace("-", "▲")

    # --- 座席データ
    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        msg2["座席"] = textwrap.dedent(f"""
            *【座席データ】*
            \t# 席：順位分布(平順) / 役満 #
            \t{data['東家-順位分布']} / {data['東家-役満和了']}
            \t{data['南家-順位分布']} / {data['南家-役満和了']}
            \t{data['西家-順位分布']} / {data['西家-役満和了']}
            \t{data['北家-順位分布']} / {data['北家-役満和了']}
        """).replace("0.00", "-.--")
    else:
        msg2["座席"] = textwrap.dedent(f"""
            *【座席データ】*
            \t# 席：順位分布(平順) / トビ / 役満 #
            \t{data['東家-順位分布']} / {data['東家-トビ']} / {data['東家-役満和了']}
            \t{data['南家-順位分布']} / {data['南家-トビ']} / {data['南家-役満和了']}
            \t{data['西家-順位分布']} / {data['西家-トビ']} / {data['西家-役満和了']}
            \t{data['北家-順位分布']} / {data['北家-トビ']} / {data['北家-役満和了']}
        """).replace("0.00", "-.--")

    # --- 記録
    msg2["記録"] = textwrap.dedent(f"""
        *【ベストレコード】*
        \t連続トップ： {data['連続トップ']} 連続
        \t連続連対： {data['連続連対']} 連続
        \t連続ラス回避： {data['連続ラス回避']} 連続
        \t最大素点： {data['最大素点'] * 100}点
        \t最大獲得ポイント： {data['最大獲得ポイント']}pt

        *【ワーストレコード】*
        \t連続ラス： {data['連続ラス']} 連続
        \t連続逆連対： {data['連続逆連対']} 連続
        \t連続トップなし： {data['連続トップなし']} 連続
        \t最小素点： {data['最小素点'] * 100}点
        \t最小獲得ポイント： {data['最小獲得ポイント']}pt
    """).replace("-", "▲")
    msg2["記録"] = msg2["記録"].replace("： 0 連続", "： ----").replace("： 1 連続", "： ----")

    if not df_grandslam.empty:
        msg2["記録"] += "\n*【役満和了】*\n"
        for x in df_grandslam.itertuples():
            msg2["記録"] += f"\t{x.matter}\t{x.count}回\n"

    if not df_regulations.query("type == 1").empty:
        msg2["記録"] += "\n*【卓外ポイント】*\n"
        for x in df_regulations.query("type == 1").itertuples():
            ex_point = str(x.ex_point).replace("-", "▲")
            msg2["記録"] += f"\t{x.matter}\t{x.count}回 ({ex_point}pt)\n"

    if not df_regulations.query("type == 2").empty:
        msg2["記録"] += "\n*【その他】*\n"
        for x in df_regulations.query("type == 2").itertuples():
            msg2["記録"] += f"\t{x.matter}\t{x.count}回\n"

    # --- 戦績
    if g.opt.game_results:
        df = d.aggregate.game_details()
        if g.opt.verbose:
            msg2["戦績"] = "\n*【戦績】*\n"
            for p in df["playtime"].unique():
                x = df.query("playtime == @p")

                if g.opt.individual:
                    if g.opt.guest_skip and g.opt.unregistered_replace and any(x["guest_count"] >= 2):
                        continue
                    if any(x["name"] == g.prm.player_name):
                        msg2["戦績"] += "{}{}\n".format(
                            p.replace("-", "/"),
                            "\t(2ゲスト戦)" if any(x["guest_count"] >= 2) else "",
                        )
                    else:
                        continue
                else:
                    if any(x["name"] == g.prm.player_name):
                        msg2["戦績"] += "{}\n".format(
                            p.replace("-", "/"),
                        )
                    else:
                        continue

                # 表示内容
                for seat, idx in list(zip(g.wind, range(len(g.wind)))):
                    if len(x) >= 4:
                        seat_data = x.iloc[idx].to_dict()
                        msg2["戦績"] += "\t{}： {} {}位 {:>7}点 ({:>+5.1f}pt) {}\n".format(
                            seat,
                            seat_data["表示名"],
                            seat_data["rank"],
                            seat_data["rpoint"] * 100,
                            seat_data["point"],
                            seat_data["grandslam"],
                        ).replace("-", "▲")
                    else:   # todo: チーム戦の結果にゲストの記録がないパターン
                        msg2["戦績"] += "\tゲスト対戦ゲーム\n"
                        break
        else:
            if g.opt.individual:
                msg2["戦績"] = f"\n*【戦績】* （{g.cfg.setting.guest_mark.strip()}：2ゲスト戦）\n"
            else:
                msg2["戦績"] = "\n*【戦績】* \n"

            for p in df["playtime"].unique():
                x = df.query("playtime == @p")

                if g.opt.individual:
                    if g.opt.guest_skip and g.opt.unregistered_replace and any(x["guest_count"] >= 2):
                        continue
                    # 個人戦集計
                    for _, seat_data in x.iterrows():
                        if seat_data["name"] == g.prm.player_name:
                            msg2["戦績"] += "\t{}{} \t{}位 {:>7}点 ({:>+5.1f}pt) {}\n".format(
                                f"{g.cfg.setting.guest_mark.strip()} " if seat_data["guest_count"] >= 2 else "",
                                seat_data["playtime"].replace("-", "/"),
                                seat_data["rank"],
                                seat_data["rpoint"] * 100,
                                seat_data["point"],
                                seat_data["grandslam"],
                            ).replace("-", "▲")
                else:
                    # チーム戦集計
                    for _, seat_data in x.iterrows():
                        if seat_data["name"] == g.prm.player_name:
                            msg2["戦績"] += "\t{} \t{}位 {:>7}点 ({:>+5.1f}pt) {}\n".format(
                                seat_data["playtime"].replace("-", "/"),
                                seat_data["rank"],
                                seat_data["rpoint"] * 100,
                                seat_data["point"],
                                seat_data["grandslam"],
                            ).replace("-", "▲")

    # --- 対戦結果
    if g.opt.versus_matrix:
        df = d.aggregate.versus_matrix()
        msg2["対戦"] = "\n*【対戦結果】*\n"
        for _, r in df.iterrows():
            msg2["対戦"] += f"\t{r['vs_表示名']}：{r['game']} 戦 {r['win']} 勝 {r['lose']} 敗 ({r['win%']:6.2f}%)\n"

    return (textwrap.dedent(msg1), msg2)
