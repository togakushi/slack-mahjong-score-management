import re

import lib.function as f
import lib.database as d
from lib.function import global_value as g


def aggregation():
    """
    各プレイヤーの通算ポイントを表示

    Returns
    -------
    msg2 : text
        検索条件などの情報

    msg : dict
        集計結果

    file_list : dict
        ファイル出力用path
    """

    ### データ収集 ###
    game_info = d.aggregate.game_info()
    df_summary = d.aggregate.game_summary()
    df_game = d.aggregate.game_details()
    df_grandslam = df_game.query("grandslam != ''")

    df_grandslam = df_grandslam.rename(
        columns = {
            "プレイヤー名": "name", "grandslam": "和了役", "playtime": "日時",
        })
    df_grandslam["和了者"] = df_grandslam["表示名"].apply(lambda x: x.strip())

    ### 表示 ###
    # --- 情報ヘッダ
    add_text = ""
    msg2 = "*【成績サマリ】*\n"
    if not g.config["mahjong"].getboolean("ignore_flying", False):
        add_text = " / トバされた人（延べ）： {} 人".format(
            df_summary["トビ"].sum(),
        )
    msg2 += f.message.header(game_info, vars(g.opt), vars(g.prm), add_text, 1)

    if df_summary.empty:
        return(msg2, {}, {})

    # --- 集計結果
    msg = {}
    msg_memo = ""

    if not g.opt.score_comparisons: # 通常表示
        if g.config["mahjong"].getboolean("ignore_flying", False): # トビカウントなし
            header_list = ["名前", "通算", "平均", "順位分布"]
            filter_list = ["名前", "ゲーム数", "通算", "平均", "1位", "2位", "3位", "4位", "平順"]
        else: # トビカウントあり
            header_list = ["名前", "通算", "平均", "順位分布", "トビ"]
            filter_list = ["名前", "ゲーム数", "通算", "平均", "1位", "2位", "3位", "4位", "平順", "トビ"]
        # メモ表示
        if len(df_grandslam) != 0:
            msg_memo = "*【メモ】*\n"
            for _, v in df_grandslam.iterrows():
                msg_memo += "\t{} ： {} （{}）\n".format(
                    v["日時"].replace("-", "/"), v["和了役"], v["和了者"],
                )
    else: # 差分表示
        df_grandslam = df_grandslam[:0] # 非表示のため破棄
        header_list = ["名前", "通算", "平均", "点差"]
        filter_list = ["名前", "ゲーム数", "通算", "点差"]

    # --- メッセージ整形
    df_summary = df_summary.rename(columns={"プレイヤー名": "名前"})
    step = 50
    step_count = []
    last_line = len(df_summary)

    for i in range(int(last_line / step + 1)): # step行毎に分割
        s_line = i * step
        e_line = (i + 1) * step

        if last_line - e_line < step / 2: # 最終ブロックがstep/2で収まるならまとめる
            step_count.append((s_line, last_line))
            break
        step_count.append((s_line, e_line))

    for s_line, e_line in step_count:
        t = df_summary[s_line:e_line].filter(
                items = header_list
            ).to_markdown(
                index = False,
                tablefmt = "simple",
                numalign = "right",
                maxheadercolwidths = 8,
                floatfmt = ("", "+.1f", "+.1f", "", ".2f")
            )
        msg[s_line] = "```\n" + re.sub(r" -([0-9]+)", r"▲\1", t) + "```\n" # マイナスを記号に置換

    # メモ追加
    if msg_memo:
        msg["メモ"] = msg_memo

    # --- ファイル出力
    df_summary = df_summary.filter(items = filter_list)
    df_grandslam = df_grandslam.filter(items = ["日時", "和了役", "和了者"])

    match g.opt.format.lower():
        case "csv":
            file_list = {
                "集計結果": f.common.save_output(df_summary, "csv", "summary.csv"),
                "役満和了": f.common.save_output(df_grandslam, "csv", "grandslam.csv"),
            }
        case "text" | "txt":
            file_list = {
                "集計結果": f.common.save_output(df_summary, "txt", "summary.txt"),
                "役満和了": f.common.save_output(df_grandslam, "txt", "grandslam.txt"),
            }
        case _:
            file_list = {}

    return(msg2, msg, file_list)
