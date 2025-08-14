"""
libs/commands/results/summary.py
"""

from typing import cast

import libs.global_value as g
from cls.types import GameInfoDict
from integrations.protocols import MessageParserProtocol
from libs.data import aggregate, loader
from libs.functions import message
from libs.utils import formatter


def aggregation(m: MessageParserProtocol) -> bool:
    """各プレイヤーの通算ポイントを表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- データ収集
    game_info: GameInfoDict = aggregate.game_info()
    df_summary = aggregate.game_summary(drop_items=["rank_distr2"])
    df_game = loader.read_data("summary/details.sql")
    df_remarks = loader.read_data("remarks.info.sql")
    df_remarks = df_remarks[df_remarks["playtime"].isin(df_game["playtime"].unique())]

    if g.params.get("anonymous"):
        col = "name" if g.params.get("individual") else "team"
        mapping_dict = formatter.anonymous_mapping(df_game["name"].unique().tolist())
        df_game["name"] = df_game["name"].replace(mapping_dict)
        df_summary[col] = df_summary[col].replace(mapping_dict)
        df_remarks["name"] = df_remarks["name"].replace(mapping_dict)

    df_summary = formatter.df_rename(df_summary)

    # --- 表示
    # 情報ヘッダ
    if g.params.get("individual"):  # 個人集計
        headline_title = "成績サマリ"
        column_name = "名前"
    else:  # チーム集計
        headline_title = "チーム成績サマリ"
        column_name = "チーム"

    add_text = "" if g.cfg.mahjong.ignore_flying else f" / トバされた人（延べ）：{df_summary["トビ"].sum()} 人"
    header_text = message.header(game_info, m, add_text, 1)
    m.post.headline = header_text

    if df_summary.empty:
        return False

    # 集計結果
    msg: dict = {}

    if g.params.get("score_comparisons"):  # 差分表示
        header_list = ["#", column_name, "通算", "順位差", "トップ差"]
        filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]
    else:  # 通常表示
        header_list = [column_name, "通算", "平均", "順位分布", "トビ"]
        filter_list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "トビ"]
        if g.cfg.mahjong.ignore_flying:  # トビカウントなし
            header_list.remove("トビ")
            filter_list.remove("トビ")

    # メッセージ整形
    msg.update(formatter.pd_to_dict(df_summary.filter(items=header_list), step=40, codeblock=True))

    # メモ追加
    df_yakuman = df_remarks.query("type == 0").drop(columns=["type", "ex_point"])
    if not df_yakuman.empty:
        msg["役満和了"] = "\n".join([
            f"\t{str(v["playtime"]).replace("-", "/")}：{v["matter"]} （{v["name"]}）"
            for _, v in df_yakuman.iterrows()
        ])

    df_regulations = df_remarks.query("type == 1").drop(columns=["type"])
    if not df_regulations.empty:
        msg["卓外ポイント"] = "\n".join([
            f"\t{str(v["playtime"]).replace("-", "/")}：{v["matter"]} {str(v["ex_point"]).replace("-", "▲")}pt（{v["name"]}）"
            for _, v in df_regulations.iterrows()
        ])

    df_others = df_remarks.query("type == 2").drop(columns=["type", "ex_point"])
    if not df_others.empty:
        msg["その他"] = "\n".join([
            f"\t{str(v["playtime"]).replace("-", "/")}：{v["matter"]} （{v["name"]}）"
            for _, v in df_others.iterrows()
        ])

    # --- ファイル出力
    match cast(str, g.params.get("format", "default")).lower():
        case "csv":
            extension = "csv"
        case "text" | "txt":
            extension = "txt"
        case _:
            extension = ""

    file_list: list = []
    if extension:
        if not df_summary.empty:
            headline = headline_title + header_text
            df_summary = df_summary.filter(items=filter_list).fillna("*****")
            prefix = f"{g.params["filename"]}" if g.params.get("filename") else "summary"
            file_list.append({"集計結果": formatter.save_output(df_summary, extension, f"{prefix}.{extension}", headline)})
        if not df_yakuman.empty:
            headline = "【役満和了】\n" + header_text
            df_yakuman = formatter.df_rename(df_yakuman, kind=0)
            prefix = f"{g.params["filename"]}_yakuman" if g.params.get("filename") else "yakuman"
            file_list.append({"役満和了": formatter.save_output(df_yakuman, extension, f"{prefix}.{extension}", headline)})
        if not df_regulations.empty:
            headline = "【卓外ポイント】\n" + header_text
            df_regulations = formatter.df_rename(df_regulations, short=False, kind=1)
            prefix = f"{g.params["filename"]}_regulations" if g.params.get("filename") else "regulations"
            file_list.append({"卓外ポイント": formatter.save_output(df_regulations, extension, f"{prefix}.{extension}", headline)})
        if not df_others.empty:
            headline = "【その他】\n" + header_text
            df_others = formatter.df_rename(df_others, kind=2)
            prefix = f"{g.params["filename"]}_others" if g.params.get("filename") else "others"
            file_list.append({"その他": formatter.save_output(df_others, extension, f"{prefix}.{extension}", headline)})
    else:
        file_list.append({"dummy": ""})

    m.post.message = msg
    m.post.file_list = file_list
    m.post.summarize = True
    return True
