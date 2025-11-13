"""
libs/commands/results/summary.py
"""

from typing import TYPE_CHECKING, cast

import libs.global_value as g
from libs.data import aggregate, loader
from libs.datamodels import GameInfo
from libs.functions import message
from libs.types import StyleOptions
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
    df_summary = aggregate.game_summary(drop_items=["rank_distr1"])
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

    add_text = "" if g.cfg.mahjong.ignore_flying else f" / トバされた人（延べ）：{df_summary["飛"].sum()} 人"
    header_text = message.header(game_info, m, add_text, 1)
    m.post.headline = {headline_title: header_text}

    if df_summary.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    # 集計結果
    header_list = [column_name, "通算", "平均", "順位分布", "飛"]
    filter_list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "飛"]
    if g.cfg.mahjong.ignore_flying:  # トビカウントなし
        header_list.remove("飛")
        filter_list.remove("飛")
    m.set_data("通算ポイント", df_summary.filter(items=header_list), StyleOptions(codeblock=True, summarize=True))

    # メモ追加
    df_yakuman = formatter.df_rename(df_remarks.query("type == 0").drop(columns=["type", "ex_point"]), kind=0)
    df_regulations = formatter.df_rename(df_remarks.query("type == 1").drop(columns=["type"]), kind=1)
    df_others = formatter.df_rename(df_remarks.query("type == 2").drop(columns=["type", "ex_point"]), kind=2)

    if not df_yakuman.empty:
        m.set_data("役満和了", df_yakuman, StyleOptions())
    if not df_regulations.empty:
        m.set_data("卓外ポイント", df_regulations, StyleOptions())
    if not df_others.empty:
        m.set_data("その他", df_others, StyleOptions())

    # --- ファイル出力
    match cast(str, g.params.get("format", "default")).lower():
        case "csv":
            extension = "csv"
        case "text" | "txt":
            extension = "txt"
        case _:
            return

    m.post.message.clear()  # テキストデータは破棄
    if not df_summary.empty:
        file_path = converter.save_output(
            df=df_summary.filter(items=filter_list).fillna("*****"),
            kind=extension,
            filename=f"summary.{extension}",
            headline=f"【{headline_title}】\n{header_text}",
            suffix="summary",
        )
        if file_path:
            m.set_data("集計結果", file_path, StyleOptions())
    if not df_yakuman.empty:
        file_path = converter.save_output(
            df=formatter.df_rename(df_yakuman, kind=0),
            kind=extension,
            filename=f"yakuman.{extension}",
            headline=f"【役満和了】\n{header_text}",
            suffix="yakuman",
        )
        if file_path:
            m.set_data("役満和了", file_path, StyleOptions())
    if not df_regulations.empty:
        file_path = converter.save_output(
            df=formatter.df_rename(df_regulations, short=False, kind=1),
            kind=extension,
            filename=f"regulations.{extension}",
            headline=f"【卓外ポイント】\n{header_text}",
            suffix="regulations",
        )
        if file_path:
            m.set_data("卓外ポイント", file_path, StyleOptions())
    if not df_others.empty:
        file_path = converter.save_output(
            df=formatter.df_rename(df_others, kind=2),
            kind=extension,
            filename=f"others.{extension}",
            headline=f"【その他】\n{header_text}",
            suffix="others",
        )
        if file_path:
            m.set_data("その他", file_path, StyleOptions())


def difference(m: "MessageParserProtocol"):
    """各プレイヤーのポイント差分を表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ収集
    game_info = GameInfo()
    df_summary = aggregate.game_summary(drop_items=["rank_distr1"])
    df_game = loader.read_data("SUMMARY_DETAILS")

    # インデックスの振りなおし
    df_summary.reset_index(inplace=True, drop=True)
    df_summary.index += 1

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df_game["name"].unique().tolist())
        df_game["name"] = df_game["name"].replace(mapping_dict)
        df_summary["name"] = df_summary["name"].replace(mapping_dict)

    df_summary = formatter.df_rename(df_summary)

    # 情報ヘッダ
    if g.params.get("individual"):  # 個人集計
        headline_title = "成績サマリ"
        column_name = "名前"
    else:  # チーム集計
        headline_title = "チーム成績サマリ"
        column_name = "チーム"

    add_text = "" if g.cfg.mahjong.ignore_flying else f" / トバされた人（延べ）：{df_summary["飛"].sum()} 人"
    header_text = message.header(game_info, m, add_text, 1)
    m.post.headline = {headline_title: header_text}

    if df_summary.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    # 集計結果
    header_list = ["#", column_name, "通算", "順位差", "トップ差"]
    filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]
    match cast(str, g.params.get("format", "default")).lower():
        case "csv":
            data = converter.save_output(
                df=df_summary.filter(items=filter_list).fillna("*****"),
                kind="csv",
                filename="summary.csv",
                headline=(headline_title + header_text),
                suffix="summary",
            )
        case "text" | "txt":
            data = converter.save_output(
                df=df_summary.filter(items=filter_list).fillna("*****"),
                kind="txt",
                filename="summary.txt",
                headline=(headline_title + header_text),
                suffix="summary",
            )
        case _:
            data = df_summary.filter(items=header_list)

    m.set_data("ポイント差分", data, StyleOptions(codeblock=True, summarize=True))
