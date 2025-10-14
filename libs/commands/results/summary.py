"""
libs/commands/results/summary.py
"""

from typing import TYPE_CHECKING, cast

import libs.global_value as g
from libs.data import aggregate, loader
from libs.datamodels import GameInfo
from libs.functions import message
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def aggregation(m: "MessageParserProtocol"):
    """各プレイヤーの通算ポイントを表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- データ収集
    game_info = GameInfo()
    df_summary = aggregate.game_summary(drop_items=["rank_distr2"])
    df_game = loader.read_data("SUMMARY_DETAILS")
    df_remarks = loader.read_data("REMARKS_INFO")

    # インデックスの振りなおし
    df_summary.reset_index(inplace=True, drop=True)
    df_summary.index += 1

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df_game["name"].unique().tolist())
        df_game["name"] = df_game["name"].replace(mapping_dict)
        df_summary["name"] = df_summary["name"].replace(mapping_dict)
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
    m.post.headline = {headline_title: header_text}

    if df_summary.empty:
        m.post.order.clear()  # 破棄
        m.status.result = False
        return

    # 集計結果
    m.post.summarize = True
    if g.params.get("score_comparisons"):  # 差分表示
        header_list = ["#", column_name, "通算", "順位差", "トップ差"]
        filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]
        m.set_data("ポイント差分", df_summary.filter(items=header_list), codeblock=True)
    else:  # 通常表示
        header_list = [column_name, "通算", "平均", "順位分布", "トビ"]
        filter_list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "トビ"]
        if g.cfg.mahjong.ignore_flying:  # トビカウントなし
            header_list.remove("トビ")
            filter_list.remove("トビ")
        m.set_data("通算ポイント", df_summary.filter(items=header_list), codeblock=True)

    # メモ追加
    df_yakuman = formatter.df_rename(df_remarks.query("type == 0").drop(columns=["type", "ex_point"]), kind=0)
    df_regulations = formatter.df_rename(df_remarks.query("type == 1").drop(columns=["type"]), kind=1)
    df_others = formatter.df_rename(df_remarks.query("type == 2").drop(columns=["type", "ex_point"]), kind=2)

    if not df_yakuman.empty:
        m.set_data("役満和了", df_yakuman)
    if not df_regulations.empty:
        m.set_data("卓外ポイント", df_regulations)
    if not df_others.empty:
        m.set_data("その他", df_others)

    # --- ファイル出力
    match cast(str, g.params.get("format", "default")).lower():
        case "csv":
            extension = "csv"
        case "text" | "txt":
            extension = "txt"
        case _:
            return

    m.post.order.clear()  # テキストデータは破棄
    if not df_summary.empty:
        file_path = converter.save_output(
            df_summary.filter(items=filter_list).fillna("*****"),
            extension,
            f"summary.{extension}",
            (headline_title + header_text),
            "summary",
        )
        if file_path:
            m.set_data("集計結果", file_path)
    if not df_yakuman.empty:
        file_path = converter.save_output(
            formatter.df_rename(df_yakuman, kind=0),
            extension,
            f"yakuman.{extension}",
            "【役満和了】\n" + header_text,
            "yakuman",
        )
        if file_path:
            m.set_data("役満和了", file_path)
    if not df_regulations.empty:
        file_path = converter.save_output(
            formatter.df_rename(df_regulations, short=False, kind=1),
            extension,
            f"regulations.{extension}",
            "【卓外ポイント】\n" + header_text,
            "regulations",
        )
        if file_path:
            m.set_data("卓外ポイント", file_path)
    if not df_others.empty:
        file_path = converter.save_output(
            formatter.df_rename(df_others, kind=2),
            extension,
            f"others.{extension}",
            "【その他】\n" + header_text,
            "others",
        )
        if file_path:
            m.set_data("その他", file_path)
