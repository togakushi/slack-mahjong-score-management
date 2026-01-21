"""
libs/commands/ranking/ranking.py
"""

from typing import TYPE_CHECKING, cast

import pandas as pd

import libs.global_value as g
from libs.data import loader
from libs.datamodels import GameInfo
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

    df = (
        pd.concat(
            [
                loader.read_data("RESULTS_INFO").query("id==0").drop(columns=["id", "seat"]),
                loader.read_data("RECORD_INFO").query("id==0").drop(columns=["id", "seat", "name"]),
            ],
            axis=1,
        )
        .drop(columns=["first_game", "last_game", "first_comment", "last_comment"])
        .query("count>=@g.params['stipulated']")
    ).copy()

    if df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target")}
        m.status.result = False
        return

    df["participation_rate"] = df["count"] / game_info.count  # ゲーム参加率
    df["avg_balance"] = df["score"] * 100 / df["count"]  # 平均収支
    df["rank1_rate"] = df["rank1"] / df["count"]  # トップ率
    df["top2_rate"] = (df["rank1"] + df["rank2"]) / df["count"]  # 連対率
    df["top3_rate"] = (df["rank1"] + df["rank2"] + df["rank3"]) / df["count"]  # ラス回避率
    df["flying_rate"] = df["flying"] / df["count"]  # トビ率
    df["yakuman_rate"] = df["yakuman"] / df["count"]  # 役満和了率
    if g.params.get("mode") == 3:
        df["rank_distr"] = [f"{x.rank1}-{x.rank2}-{x.rank3}" for x in df.itertuples()]
    else:
        df["rank_distr"] = [f"{x.rank1}-{x.rank2}-{x.rank3}-{x.rank4}" for x in df.itertuples()]

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    # 集計
    data: dict[str, pd.DataFrame] = {}
    ranked = int(g.params.get("ranked", g.cfg.ranking.ranked))  # noqa: F841

    data["ゲーム参加率"] = (
        pd.DataFrame(
            {
                "rank": df["participation_rate"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "participation_rate": [f"{x.participation_rate:.2%}" for x in df.itertuples()],
                "count": df["count"],
                "total_count": game_info.count,
            }
        )
        .sort_values("rank")
        .query("rank <= @ranked")
    )
    data["通算ポイント"] = (
        pd.DataFrame(
            {
                "rank": df["total_point"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "total_point": [f"{x.total_point:+.1f}pt".replace("-", "▲") for x in df.itertuples()],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["平均ポイント"] = (
        pd.DataFrame(
            {
                "rank": df["avg_point"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "avg_point": [f"{x.avg_point:+.1f}pt".replace("-", "▲") for x in df.itertuples()],
                "total_point": [f"{x.total_point:+.1f}pt".replace("-", "▲") for x in df.itertuples()],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["平均収支"] = (
        pd.DataFrame(
            {
                "rank": df["avg_balance"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "avg_balance": [f"{x.avg_balance:+.1f}点".replace("-", "▲") for x in df.itertuples()],
                "rpoint_avg": [f"{cast(float, x.rpoint_avg) * 100:+.1f}点".replace("-", "▲") for x in df.itertuples()],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["トップ率"] = (
        pd.DataFrame(
            {
                "rank": df["rank1_rate"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "rank1_rate": [f"{x.rank1_rate:.2%}" for x in df.itertuples()],
                "rank1": df["rank1"],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    if g.params.get("mode") == 3:
        data["ラス回避率"] = (
            pd.DataFrame(
                {
                    "rank": df["top2_rate"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top2_rate": [f"{x.top2_rate:.2%}" for x in df.itertuples()],
                    "top2": df["rank1"] + df["rank2"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked")
        )
    else:
        data["連対率"] = (
            pd.DataFrame(
                {
                    "rank": df["top2_rate"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top2_rate": [f"{x.top2_rate:.2%}" for x in df.itertuples()],
                    "top2": df["rank1"] + df["rank2"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked")
        )
        data["ラス回避率"] = (
            pd.DataFrame(
                {
                    "rank": df["top3_rate"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top3_rate": [f"{x.top3_rate:.2%}" for x in df.itertuples()],
                    "top3": df["rank1"] + df["rank2"] + df["rank3"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked")
        )
    data["トビ率"] = (
        pd.DataFrame(
            {
                "rank": df["flying_rate"].rank(ascending=True, method="dense").astype("int"),
                "name": df["name"],
                "flying_rate": [f"{x.flying_rate:.2%}" for x in df.itertuples()],
                "flying": df["flying"],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["平均順位"] = (
        pd.DataFrame(
            {
                "rank": df["rank_avg"].rank(ascending=True, method="dense").astype("int"),
                "name": df["name"],
                "rank_avg": [f"{x.rank_avg:.2f}" for x in df.itertuples()],
                "rank_distr": df["rank_distr"],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["役満和了率"] = (
        pd.DataFrame(
            {
                "rank": df["yakuman_rate"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "yakuman_rate": [f"{x.yakuman_rate:.2%}" for x in df.itertuples()],
                "yakuman": df["yakuman"],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked and yakuman > 0")
    )
    data["最大素点"] = (
        pd.DataFrame(
            {
                "rank": df["rpoint_max"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "rpoint_max": [f"{cast(float, x.rpoint_max) * 100}点".replace("-", "▲") for x in df.itertuples()],
                "point_max": [f"{x.point_max:+.1f}pt".replace("-", "▲") for x in df.itertuples()],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked")
    )
    data["連続トップ"] = (
        pd.DataFrame(
            {
                "rank": df["top1_max"].rank(ascending=False, method="dense").astype("int"),
                "name": df["name"],
                "top1_max": df["top1_max"],
                "count": df["count"],
            }
        )
        .sort_values(by=["rank", "count"], ascending=[True, False])
        .query("rank <= @ranked and top1_max > 1")
    )
    if g.params.get("mode") == 3:
        data["連続ラス回避"] = (
            pd.DataFrame(
                {
                    "rank": df["top2_max"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top2_max": df["top2_max"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked and top2_max > 1")
        )
    else:
        data["連続連対"] = (
            pd.DataFrame(
                {
                    "rank": df["top2_max"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top2_max": df["top2_max"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked and top2_max > 1")
        )
        data["連続ラス回避"] = (
            pd.DataFrame(
                {
                    "rank": df["top3_max"].rank(ascending=False, method="dense").astype("int"),
                    "name": df["name"],
                    "top3_max": df["top3_max"],
                    "count": df["count"],
                }
            )
            .sort_values(by=["rank", "count"], ascending=[True, False])
            .query("rank <= @ranked and top3_max > 1")
        )

    # 項目整理
    if g.cfg.mahjong.ignore_flying or g.cfg.dropitems.ranking & g.cfg.dropitems.flying:
        data.pop("トビ率")
    if g.cfg.dropitems.ranking & g.cfg.dropitems.yakuman:
        data.pop("役満和了率")

    for msg, df_data in data.items():
        if msg in g.cfg.dropitems.ranking:  # 非表示項目
            continue
        if df_data.empty:  # 対象者なし
            continue
        m.set_data(
            df_data,
            StyleOptions(
                title=msg,
                data_kind=StyleOptions.DataKind.RANKING,
                rename_type=StyleOptions.RenameType.SHORT,
                codeblock=True,
                show_index=False,
            ),
        )

    m.post.headline = {title: message.header(game_info, m, "", 1)}
