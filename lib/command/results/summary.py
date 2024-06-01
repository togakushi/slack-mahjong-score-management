import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def aggregation(argument, command_option):
    """
    各プレイヤーの累積ポイントを表示

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg2 : text
        検索条件などの情報

    msg : dict
        集計結果
    """

    ### データ収集 ###
    params = f.configure.get_parameters(argument, command_option)
    total_game_count, first_game, last_game = d.aggregate.game_count(argument, command_option)
    summary_df = d.aggregate.game_summary(argument, command_option)
    game_df = d.aggregate.game_details(argument, command_option)

    ### 表示 ###
    # --- 情報ヘッダ
    msg2 = "*【成績サマリ】*\n"
    if params["target_count"] == 0: # 直近指定がない場合は検索範囲を付ける
        msg2 += f"\t検索範囲：{params['starttime_hms']} ～ {params['endtime_hms']}\n"
    if total_game_count != 0:
        msg2 += f"\t最初のゲーム：{first_game}\n\t最後のゲーム：{last_game}\n".replace("-", "/")
        if params["player_name"]:
            msg2 += f"\t総ゲーム数：{total_game_count} 回"
        else:
            msg2 += f"\tゲーム数：{total_game_count} 回"

        if g.config["mahjong"].getboolean("ignore_flying", False):
            msg2 += "\n"
        else:
            msg2 += " / トバされた人（延べ）： {} 人\n".format(
                summary_df["flying"].sum(),
            )
        msg2 += "\t" + f.message.remarks(command_option)
    else: # 結果が0件のとき
        msg2 += "\t" + f.message.remarks(command_option)
        return(msg2, f.message.no_hits(argument, command_option))

    # --- 集計結果
    padding = c.member.CountPadding(list(summary_df["表示名"].unique())) -7
    message = ""

    if command_option["score_comparisons"]: # 差分表示
        header = f"\n```\n# 名前{' ' * padding} ： 累積    / 点差 #\n"
        for _, v in summary_df.iterrows():
            message += "{}： {:>+6.1f} / {:>5.1f}\n".format(
                v["表示名"], v["pt_total"], v["pt_diff"],
            ).replace("-", "▲")
    else: # 通常表示
        if g.config["mahjong"].getboolean("ignore_flying", False): # トビカウントなし
            header = f"\n```\n# 名前{' ' * padding} ：  累積   (平均) / 順位分布 (平均) #\n"
            for i, v in summary_df.iterrows():
                message += "{}： {} ({}) / {} ({:1.2f})\n".format(
                    v["表示名"],
                    str(f"{v['pt_total']:>+6.1f}").replace("-", "▲"),
                    str(f"{v['pt_avg']:>+5.1f}").replace("-", "▲"),
                    v["rank_distr"], v["rank_avg"],
                )
        else: # トビカウントあり
            header = f"\n```\n# 名前{' ' * padding} ：  累積   (平均) / 順位分布 (平均) / トビ #\n"
            for i, v in summary_df.iterrows():
                message += "{}： {} ({}) / {} ({:1.2f}) / {}\n".format(
                    v["表示名"],
                    str(f"{v['pt_total']:>+6.1f}").replace("-", "▲"),
                    str(f"{v['pt_avg']:>+5.1f}").replace("-", "▲"),
                    v["rank_distr"], v["rank_avg"], v["flying"],
                )

        # メッセージをstep行単位のブロックに分割
        step = 50
        msg = {}
        for count in range(int(len(message.splitlines()) / step) + 1):
            msg[count] = "\n".join(message.splitlines()[count * step:(count + 1) * step])

        # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
        if count >= 1 and step / 2 > len(msg[count].splitlines()):
            msg[count - 1] += "\n" + msg.pop(count)

        # ヘッダ+コードブロック追加
        for i in msg.keys():
            msg[i] = header + msg[i] + "\n```\n"

        # --- メモ表示
        grandslam_df = game_df.query("grandslam != ''")
        if len(grandslam_df) != 0:
            msg["メモ"] = "*【メモ】*\n"
            for _, v in grandslam_df.iterrows():
                msg["メモ"] += f"\t{v['playtime']} {v['表示名']} {v['grandslam']}\n"

    return(msg2, msg)
