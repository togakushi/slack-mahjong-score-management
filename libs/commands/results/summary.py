"""
libs/commands/results/summary.py
"""

from copy import copy
from typing import TYPE_CHECKING

import libs.global_value as g
from libs.data import aggregate, loader
from libs.datamodels import GameInfo
from libs.functions import message
from libs.types import StyleOptions
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType


def aggregation(m: "MessageParserProtocol"):
    """各プレイヤーの通算ポイントを表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- データ収集
    data: "MessageType"
    options: StyleOptions
    game_info = GameInfo()
    df_summary = aggregate.game_summary()
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

    # 情報ヘッダ
    if g.params.get("individual"):  # 個人集計
        headline_title = "成績サマリ"
        column_name = "名前"
    else:  # チーム集計
        headline_title = "チーム成績サマリ"
        column_name = "チーム"

    add_text = "" if g.cfg.mahjong.ignore_flying else f" / トバされた人（延べ）：{df_summary['飛'].sum()} 人"
    header_text = message.header(game_info, m, add_text, 1)
    m.post.headline = {headline_title: header_text}

    if df_summary.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    # 通算ポイント
    options = StyleOptions(
        title="通算ポイント",
        format_type=g.params["format"],
        codeblock=False,
        rename_type=StyleOptions.RenameType.SHORT,
        data_kind=StyleOptions.DataKind.POINTS_TOTAL,
    )

    header_list = [column_name, "通算", "平均", "順位分布", "飛"]
    filter_list = [column_name, "ゲーム数", "通算", "平均", "差分", "1位", "2位", "3位", "4位", "平順", "飛"]
    if g.cfg.mahjong.ignore_flying or g.cfg.dropitems.results & g.cfg.dropitems.flying:  # トビカウントなし
        header_list.remove("飛")
        filter_list.remove("飛")

    if options.format_type == "default":
        options.codeblock = True
        data = df_summary.filter(items=header_list)
    else:
        options.base_name = "summary"
        df_summary = df_summary.filter(items=filter_list).fillna("*****")
        data = converter.save_output(df_summary, options, f"【{headline_title}】\n{header_text}", "summary")
    m.set_data(data, copy(options))

    # メモ(役満和了)
    if not g.cfg.dropitems.results & g.cfg.dropitems.yakuman:
        options.title = "役満和了"
        options.data_kind = StyleOptions.DataKind.REMARKS_YAKUMAN
        df_yakuman = formatter.df_rename(df_remarks.query("type == 0").drop(columns=["type", "ex_point"]), kind=0)
        if options.format_type == "default":
            options.codeblock = False
            data = df_yakuman
        else:
            options.base_name = "yakuman"
            data = converter.save_output(df_yakuman, options, f"【役満和了】\n{header_text}", "yakuman")
        m.set_data(data, copy(options))

    # メモ(卓外清算)
    if not g.cfg.dropitems.results & g.cfg.dropitems.regulation:
        options.title = "卓外清算"
        options.data_kind = StyleOptions.DataKind.REMARKS_REGULATION
        if g.params.get("individual"):  # 個人集計
            df_regulations = formatter.df_rename(df_remarks.query("type == 2").drop(columns=["type"]), kind=1)
        else:  # チーム集計
            df_regulations = formatter.df_rename(df_remarks.query("type == 2 or type == 3").drop(columns=["type"]), kind=1)
        if options.format_type == "default":
            options.codeblock = False
            data = df_regulations
        else:
            options.base_name = "regulations"
            data = converter.save_output(df_regulations, options, f"【卓外清算】\n{header_text}", "regulations")
        m.set_data(data, copy(options))

    # メモ(その他)
    if not g.cfg.dropitems.results & g.cfg.dropitems.other:
        options.title = "その他"
        options.data_kind = StyleOptions.DataKind.REMARKS_OTHER
        df_others = formatter.df_rename(df_remarks.query("type == 1").drop(columns=["type", "ex_point"]), kind=2)
        if options.format_type == "default":
            data = df_others
        else:
            options.base_name = "others"
            data = converter.save_output(df_others, options, f"【その他】\n{header_text}", "others")
        m.set_data(data, copy(options))


def difference(m: "MessageParserProtocol"):
    """各プレイヤーのポイント差分を表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ収集
    data: "MessageType"
    game_info = GameInfo()
    df_summary = aggregate.game_summary()
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

    add_text = "" if g.cfg.mahjong.ignore_flying else f" / トバされた人（延べ）：{df_summary['飛'].sum()} 人"
    header_text = message.header(game_info, m, add_text, 1)
    m.post.headline = {headline_title: header_text}

    if df_summary.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    # 集計結果
    header_list = ["#", column_name, "通算", "順位差", "トップ差"]
    filter_list = [column_name, "ゲーム数", "通算", "順位差", "トップ差"]
    match g.params.get("format", "default").lower():
        case "csv":
            data = converter.save_output(
                df_summary.filter(items=filter_list).fillna("*****"),
                StyleOptions(format_type="csv", base_name="summary"),
                f"【{headline_title}】\n{header_text}",
            )
        case "text" | "txt":
            data = converter.save_output(
                df_summary.filter(items=filter_list).fillna("*****"),
                StyleOptions(format_type="txt", base_name="summary"),
                f"【{headline_title}】\n{header_text}",
            )
        case _:
            data = df_summary.filter(items=header_list)

    m.set_data(data, StyleOptions(codeblock=True, summarize=True))
