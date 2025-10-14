"""
libs/commands/ranking/ranking.py
"""

from typing import TYPE_CHECKING

import pandas as pd

import libs.global_value as g
from cls.score import GameInfo
from libs.data import aggregate, loader
from libs.functions import message
from libs.types import StyleOptions
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def aggregation(m: "MessageParserProtocol"):
    """ランキングデータを生成

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 情報ヘッダ
    if g.params.get("individual"):  # 個人集計
        title = "ランキング"
    else:  # チーム集計
        title = "チームランキング"

    # データ取得
    game_info = GameInfo()
    if not game_info.count:  # 検索結果が0件のとき
        m.post.headline = {title: message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    result_df = loader.read_data("RANKING_AGGREGATE")
    if result_df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target")}
        m.status.result = False
        return

    df = pd.merge(
        result_df, aggregate.ranking_record(),
        on=["name", "name"],
        suffixes=["", "_x"]
    )
    df["rank"] = 0  # 順位表示用カラム
    df["total_count"] = game_info.count  # 集計ゲーム数
    df["participation_rate"] = df["game_count"] / df["total_count"]  # 参加率
    df["balance_avg"] = df["rpoint_avg"] - g.cfg.mahjong.origin_point * 100  # 平均収支

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    # 集計
    data: dict[str, pd.DataFrame] = {}
    ranked = int(g.params.get("ranked", g.cfg.ranking.ranked))  # pylint: disable=unused-variable  # noqa: F841

    # ゲーム参加率
    filter_item = ["rank", "name", "participation_rate", "game_count", "total_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["participation_rate", "game_count"], ascending=[False, False])
    work_df["rank"] = df["participation_rate"].rank(ascending=False, method="dense").astype("int")
    data["ゲーム参加率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 通算ポイント
    filter_item = ["rank", "name", "point_sum", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["point_sum", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["point_sum"].rank(ascending=False, method="dense").astype("int")
    data["通算ポイント"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 平均ポイント
    filter_item = ["rank", "name", "point_avg", "point_sum", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["point_avg", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["point_avg"].rank(ascending=False, method="dense").astype("int")
    data["平均ポイント"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 平均収支
    filter_item = ["rank", "name", "balance_avg", "rpoint_avg", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["rpoint_avg", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["balance_avg"].rank(ascending=False, method="dense").astype("int")
    data["平均収支"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # トップ率
    filter_item = ["rank", "name", "rank1_rate", "rank1", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["rank1_rate", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["rank1_rate"].rank(ascending=False, method="dense").astype("int")
    data["トップ率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 連対率
    filter_item = ["rank", "name", "top2_rate", "top2", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["top2_rate", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["top2_rate"].rank(ascending=False, method="dense").astype("int")
    data["連対率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # ラス回避率
    filter_item = ["rank", "name", "top3_rate", "top3", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["top3_rate", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["top3_rate"].rank(ascending=False, method="dense").astype("int")
    data["ラス回避率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # トビ率
    filter_item = ["rank", "name", "flying_rate", "flying", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["flying_rate", "game_count"], ascending=[True, False])
    work_df["rank"] = work_df["flying_rate"].rank(ascending=True, method="dense").astype("int")
    data["トビ率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 平均順位
    work_df = df.sort_values(by=["rank_avg", "game_count"], ascending=[True, False])
    work_df["rank"] = work_df["rank_avg"].rank(ascending=True, method="dense").astype("int")
    filter_item = ["rank", "name", "rank_avg", "rank_distr"]
    work_df = work_df.filter(items=filter_item).sort_values(by="rank", ascending=True)
    data["平均順位"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 役満和了率
    work_df = df.query("gs_count > 0")
    filter_item = ["rank", "name", "gs_rate", "gs_count", "game_count"]
    work_df = work_df.filter(items=filter_item).sort_values(by=["gs_rate", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["gs_rate"].rank(ascending=False, method="dense").astype("int")
    data["役満和了率"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 最大素点
    filter_item = ["rank", "name", "rpoint_max", "point_max", "game_count"]
    work_df = df.filter(items=filter_item).sort_values(by=["rpoint_max", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["rpoint_max"].rank(ascending=False, method="dense").astype("int")
    data["最大素点"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 連続トップ
    work_df = df.query("max_top > 1")
    filter_item = ["rank", "name", "max_top", "game_count"]
    work_df = work_df.filter(items=filter_item).sort_values(by=["max_top", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["max_top"].rank(ascending=False, method="dense").astype("int")
    data["連続トップ"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 連続連対
    work_df = df.query("max_top2 > 1")
    filter_item = ["rank", "name", "max_top2", "game_count"]
    work_df = work_df.filter(items=filter_item).sort_values(by=["max_top2", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["max_top2"].rank(ascending=False, method="dense").astype("int")
    data["連続連対"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 連続ラス回避
    work_df = df.query("max_top3 > 1")
    filter_item = ["rank", "name", "max_top3", "game_count"]
    work_df = work_df.filter(items=filter_item).sort_values(by=["max_top3", "game_count"], ascending=[False, False])
    work_df["rank"] = work_df["max_top3"].rank(ascending=False, method="dense").astype("int")
    data["連続ラス回避"] = formatter.df_rename(work_df.query("rank <= @ranked"), short=False)

    # 項目整理
    dropitems = g.cfg.dropitems.ranking
    if g.cfg.mahjong.ignore_flying:
        dropitems.append("トビ率")
    if {"役満", "役満和了"} & set(g.cfg.dropitems.ranking):
        dropitems.append("役満和了率")

    for k, v in data.items():
        if k in dropitems:  # 非表示項目
            continue
        if v.empty:  # 対象者なし
            continue
        m.set_data(k, v, StyleOptions(codeblock=True, show_index=False))

    m.post.headline = {title: message.header(game_info, m, "", 1)}
    m.post.key_header = True
