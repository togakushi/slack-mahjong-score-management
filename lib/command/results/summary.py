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
    df_summary = d.aggregate.game_summary(argument, command_option)
    df_game = d.aggregate.game_details(argument, command_option)
    df_grandslam = df_game.query("grandslam != ''")

    # ヘッダ更新 ToDo: SQLのカラム名を変える
    df_summary = df_summary.rename(
        columns = {
            "count": "ゲーム数", "pt_total": "累積ポイント", "pt_avg": "平均ポイント",
            "1st": "1位", "2nd": "2位", "3rd": "3位", "4th": "4位", "rank_distr": "順位分布",
            "rank_avg": "平均順位", "flying": "トビ", "pt_diff": "差分",
        })
    df_summary["プレイヤー名"] = df_summary["表示名"].apply(lambda x: x.strip())
    df_grandslam = df_grandslam.rename(
        columns = {
            "プレイヤー名": "name", "grandslam": "和了役", "playtime": "日時",
        })
    df_grandslam["プレイヤー名"] = df_grandslam["表示名"].apply(lambda x: x.strip())

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
                df_summary["トビ"].sum(),
            )
        msg2 += "\t" + f.message.remarks(command_option)
    else: # 結果が0件のとき
        msg2 += f"\tゲーム数：{total_game_count} 回"
        msg2 += "\t" + f.message.remarks(command_option)
        return(msg2, None, df_summary, df_grandslam)

    # --- 集計結果
    padding = c.member.CountPadding(list(df_summary["表示名"].unique())) -7
    msg = {}
    message = ""
    msg_memo = ""

    if not command_option["score_comparisons"]: # 通常表示
        if g.config["mahjong"].getboolean("ignore_flying", False): # トビカウントなし
            header = f"\n```\n# 名前{' ' * padding} ：  累積   (平均) / 順位分布 (平均) #\n"
            filter_list = [
                "プレイヤー名", "ゲーム数", "累積ポイント", "平均ポイント",
                "1位", "2位", "3位", "4位", "平均順位",
            ]
            for i, v in df_summary.iterrows():
                message += "{}： {} ({}) / {} ({:1.2f})\n".format(
                    v["表示名"],
                    str(f"{v['累積ポイント']:>+6.1f}").replace("-", "▲"),
                    str(f"{v['平均ポイント']:>+5.1f}").replace("-", "▲"),
                    v["順位分布"], v["平均順位"],
                )
        else: # トビカウントあり
            header = f"\n```\n# 名前{' ' * padding} ：  累積   (平均) / 順位分布 (平均) / トビ #\n"
            filter_list = [
                "プレイヤー名", "ゲーム数", "累積ポイント", "平均ポイント",
                "1位", "2位", "3位", "4位", "平均順位", "トビ",
            ]
            for i, v in df_summary.iterrows():
                message += "{}： {} ({}) / {} ({:1.2f}) / {}\n".format(
                    v["表示名"],
                    str(f"{v['累積ポイント']:>+6.1f}").replace("-", "▲"),
                    str(f"{v['平均ポイント']:>+5.1f}").replace("-", "▲"),
                    v["順位分布"], v["平均順位"], v["トビ"],
                )

        # --- メモ表示
        if len(df_grandslam) != 0:
            msg_memo = "*【メモ】*\n"
            for _, v in df_grandslam.iterrows():
                msg_memo += "\t{} ： {} （{}）\n".format(
                    v["日時"].replace("-", "/"),
                    v["和了役"],
                    v["プレイヤー名"],
                )
    else: # 差分表示
        df_grandslam = df_grandslam[:0]
        header = f"\n```\n# 名前{' ' * padding} ： 累積    / 点差 #\n"
        filter_list = ["プレイヤー名", "ゲーム数", "累積ポイント", "点差"]
        for _, v in df_summary.iterrows():
            message += "{}： {} / {}\n".format(
                v["表示名"],
                str(f"{v['累積ポイント']:>+6.1f}").replace("-", "▲"),
                f"{v['差分']:>5.1f}" if type(v["差分"]) == float else v["差分"],
            )

    # --- メッセージ整形
    # メッセージをstep行単位のブロックに分割
    step = 50
    for count in range(int(len(message.splitlines()) / step) + 1):
        msg[count] = "\n".join(message.splitlines()[count * step:(count + 1) * step])

    # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
    if count >= 1 and step / 2 > len(msg[count].splitlines()):
        msg[count - 1] += "\n" + msg.pop(count)

    # ヘッダ+コードブロック追加
    for i in msg.keys():
        msg[i] = header + msg[i] + "\n```\n"

    # メモ追加
    if msg_memo:
        msg["メモ"] = msg_memo

    # --- ファイル出力用データ整形
    df_summary = df_summary.filter(items = filter_list)
    df_grandslam = df_grandslam.filter(items = ["日時", "和了役", "プレイヤー名"])

    return(msg2, msg, df_summary, df_grandslam)
