"""
libs/commands/ranking/rating.py
"""

from typing import TYPE_CHECKING

import pandas as pd

import libs.global_value as g
from integrations.protocols import CommandType
from libs.data import aggregate, loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.types import StyleOptions
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType


def aggregation(m: "MessageParserProtocol"):
    """レーティングを集計して返す

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    m.status.command_type = CommandType.RATING  # 更新

    # 情報ヘッダ
    title: str = "レーティング"
    add_text: str = ""

    if g.params.get("mode") == 3 or g.params.get("target_mode") == 3:  # todo: 未実装
        m.post.headline = {title: message.random_reply(m, "not_implemented")}
        m.status.result = False
        return

    # データ収集
    # g.params.update(guest_skip=False)  # 2ゲスト戦強制取り込み
    game_info = GameInfo()
    ranked = int(g.params.get("ranked", g.cfg.ranking.ranked))  # noqa: F841

    if not game_info.count:  # 検索結果が0件のとき
        m.post.headline = {title: message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    df_results = loader.read_data("RANKING_RESULTS").set_index("name")
    df_ratings = aggregate.calculation_rating()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final.columns = ["rate"]
    final["name"] = final.copy().index

    df = pd.merge(df_results, final, on=["name"]).sort_values(by="rate", ascending=False)
    df = df.query("count >= @g.params['stipulated']").copy()  # 足切り
    df["rank"] = 0  # 順位表示用カラム

    # 集計対象外データの削除
    if g.params.get("unregistered_replace"):  # 個人戦
        for player in df.itertuples():
            if player.name not in g.cfg.member.lists:
                df = df.copy().drop(player.Index)

    if not g.params.get("individual"):  # チーム戦
        df = df.copy().query("name != '未所属'")

    # 順位偏差 / 得点偏差
    df["point_dev"] = (df["rpoint_avg"] - df["rpoint_avg"].mean()) / df["rpoint_avg"].std(ddof=0) * 10 + 50
    df["rank_dev"] = (df["rank_avg"] - df["rank_avg"].mean()) / df["rank_avg"].std(ddof=0) * -10 + 50

    # 段位
    if g.adapter.conf.badge_grade:
        for idx in df.index:
            name = str(df.at[idx, "name"]).replace(f"({g.cfg.setting.guest_mark})", "")
            df.at[idx, "grade"] = compose.badge.grade(name, False)

    # 表示
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    if df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target")}
        m.status.result = False
        return

    df["rank"] = df["rate"].rank(ascending=False, method="dense").astype("int")
    df = formatter.df_rename2(
        df.query("rank <= @ranked").filter(items=["rank", "name", "rate", "rank_distr", "rank_avg", "rank_dev", "rpoint_avg", "point_dev", "grade"]),
        StyleOptions(),
    ).copy()

    df = df.drop(columns=[x for x in g.cfg.dropitems.ranking if x in df.columns.to_list()])  # 非表示項目

    m.post.headline = {title: message.header(game_info, m, add_text, 1)}
    options: StyleOptions = StyleOptions(
        title=title,
        data_kind=StyleOptions.DataKind.RATING,
        rename_type=StyleOptions.RenameType.SHORT,
        base_name="rating",
        format_type="default",
        summarize=False,
        codeblock=True,
    )

    data: "MessageType"
    match g.params.get("format", "default"):
        case "csv":
            options.format_type = "csv"
            data = converter.save_output(df, options, m.post.headline)
        case "text" | "txt":
            options.format_type = "txt"
            data = converter.save_output(df, options, m.post.headline)
        case _:
            options.key_title = False
            data = df

    m.set_data(data, options)
