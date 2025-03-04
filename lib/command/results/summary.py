import re

import pandas as pd

import lib.global_value as g
from lib import database as d
from lib import function as f


def aggregation():
    """各プレイヤーの通算ポイントを表示

    Returns:
        Tuple[str, dict, dict]
            - str: ヘッダ情報
            - dict: 集計データ
            - dict: 生成ファイル情報
    """

    # --- データ収集
    game_info = d.aggregate.game_info()
    df_summary = d.aggregate.game_summary(drop_items=["rank_distr2"])
    df_game = d.aggregate.game_details()

    df_grandslam = df_game.query("grandslam != ''")
    df_summary = d.common.df_rename(df_summary)

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    if g.opt.individual:  # 個人集計
        headline = "*【成績サマリ】*\n"
        column_name = "名前"
    else:  # チーム集計
        headline = "*【チーム成績サマリ】*\n"
        column_name = "チーム"

    if not g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        add_text = " / トバされた人（延べ）：{} 人".format(  # pylint: disable=consider-using-f-string
            df_summary["トビ"].sum(),
        )

    headline += f.message.header(game_info, add_text, 1)

    if df_summary.empty:
        return (headline, {}, {})

    # --- 集計結果
    msg: dict = {}
    msg_memo: str = memo_count(df_game)

    if not g.opt.score_comparisons:  # 通常表示
        header_list: list = [column_name, "通算", "平均", "順位分布", "トビ"]
        filter_list: list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "トビ"]
        if g.cfg.config["mahjong"].getboolean("ignore_flying", False):  # トビカウントなし
            header_list.remove("トビ")
            filter_list.remove("トビ")
    else:  # 差分表示
        df_grandslam = df_grandslam[:0]  # 非表示のため破棄
        msg_memo = ""  # 非表示のため破棄
        header_list = ["#", column_name, "通算", "順位差", "トップ差"]
        filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]

    # --- メッセージ整形
    step: int = 40
    step_count: list = []
    print_df = df_summary.filter(items=header_list)
    floatfmt = f.common.floatfmt_adjust(print_df)
    last_line = len(print_df)

    for i in range(int(last_line / step + 1)):  # step行毎に分割
        s_line = i * step
        e_line = (i + 1) * step

        if last_line - e_line < step / 2:  # 最終ブロックがstep/2で収まるならまとめる
            step_count.append((s_line, last_line))
            break
        step_count.append((s_line, e_line))

    for s_line, e_line in step_count:
        t = print_df[s_line:e_line].to_markdown(
            index=False,
            tablefmt="simple",
            numalign="right",
            maxheadercolwidths=8,
            floatfmt=floatfmt,
        ).replace("   nan", "******")
        msg[s_line] = "```\n" + re.sub(r"  -([0-9]+)", r" ▲\1", t) + "\n```\n"  # マイナスを記号に置換

    # メモ追加
    if msg_memo:
        msg["メモ"] = msg_memo

    # --- ファイル出力
    df_summary = df_summary.filter(items=filter_list)
    df_grandslam = df_grandslam.filter(
        items=["playtime", "grandslam", "name"]
    ).rename(
        columns={
            "playtime": "日時",
            "grandslam": "和了役",
            "name": "和了者",
        }
    )

    match g.opt.format.lower():
        case "csv":
            file_list = {
                "集計結果": f.common.save_output(df_summary, "csv", "summary.csv", headline),
                "役満和了": f.common.save_output(df_grandslam, "csv", "yakuman.csv", headline),
            }
        case "text" | "txt":
            file_list = {
                "集計結果": f.common.save_output(df_summary, "txt", "summary.txt", headline),
                "役満和了": f.common.save_output(df_grandslam, "txt", "yakuman.txt", headline),
            }
        case _:
            file_list = {}

    return (headline, msg, file_list)


def memo_count(df_game: pd.DataFrame) -> str:
    """メモ集計

    Args:
        df_game (pd.DataFrame): ゲーム情報

    Returns:
        str: 集計結果
    """

    # データ収集
    df_grandslam = df_game.query("grandslam != ''")
    df_regulations = df_game.query("type == 1")
    df_wordcount = df_game.query("type == 2" if g.undefined_word != 2 else "type != '' or type == 2")

    # メモ表示
    memo_grandslam = ""
    if not df_grandslam.empty:
        memo_grandslam = "\n*【役満和了】*\n"
        for _, v in df_grandslam.iterrows():
            memo_grandslam += "\t{}：{} （{}）\n".format(  # pylint: disable=consider-using-f-string
                v["playtime"].replace("-", "/"),
                v["grandslam"],
                v["表示名"].strip(),
            )

    memo_regulation = ""
    if not df_regulations.empty:
        memo_regulation = "\n*【卓外ポイント】*\n"
        for _, v in df_regulations.iterrows():
            memo_regulation += "\t{}：{} {}pt（{}）\n".format(  # pylint: disable=consider-using-f-string
                v["playtime"].replace("-", "/"),
                v["regulation"],
                str(v["ex_point"]).replace("-", "▲"),
                v["表示名"].strip(),
            )

    memo_wordcount = ""
    if not df_wordcount.empty:
        memo_wordcount = "\n*【その他】*\n"
        for _, v in df_wordcount.iterrows():
            memo_wordcount += "\t{}：{} （{}）\n".format(  # pylint: disable=consider-using-f-string
                v["playtime"].replace("-", "/"),
                v["regulation"],
                v["表示名"].strip(),
            )

    return (memo_grandslam + memo_regulation + memo_wordcount).strip()
