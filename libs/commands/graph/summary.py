"""
libs/commands/graph/summary.py
"""

import logging
from typing import TYPE_CHECKING, Literal, Optional, TypedDict, cast

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px  # type: ignore

import libs.global_value as g
from libs.data import loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.utils import formatter, graphutil, textutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


class GraphParams(TypedDict, total=False):
    """グラフ生成パラメータ"""

    graph_type: Literal["point", "rank", "point_hbar"]
    title_text: str
    xlabel_text: Optional[str]
    ylabel_text: Optional[str]
    total_game_count: int
    target_data: pd.DataFrame
    pivot: pd.DataFrame
    horizontal: bool  # 横棒切替許可フラグ
    save_file: str


def point_plot(m: "MessageParserProtocol"):
    """ポイント推移グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 初期化
    graph_params = GraphParams()

    # データ収集
    game_info = GameInfo()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        m.status.result = False
        return

    # 集計
    if g.params.get("search_word"):
        pivot_index = "comment"
    else:
        pivot_index = "playtime"

    pivot = pd.pivot_table(
        df, index=pivot_index, columns="name", values="point_sum"
    ).ffill()
    pivot = pivot.reindex(  # 並び替え
        target_data["name"].to_list(), axis="columns"
    )

    # グラフ生成
    graph_params.update({
        "graph_type": "point",
        "total_game_count": game_info.count,
        "target_data": target_data,
        "pivot": pivot,
        "horizontal": True,
    })

    match g.adapter.conf.plotting_backend:
        case "plotly":
            graph_params.update({"save_file": "graph.html"})
            save_file = _graph_generation_plotly(graph_params)
        case _:
            graph_params.update({"save_file": "graph.png"})
            save_file = _graph_generation(graph_params)

    file_title = graph_params.get("title_text", "").split()[0]
    m.post.file_list = [{file_title: save_file}]
    m.post.headline = {f"{file_title}グラフ": message.header(game_info, m)}


def rank_plot(m: "MessageParserProtocol"):
    """順位変動グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 初期化
    graph_params = GraphParams()

    # データ収集
    game_info = GameInfo()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        m.status.result = False
        return

    if g.params.get("search_word"):
        pivot_index = "comment"
    else:
        pivot_index = "playtime"

    # 集計
    pivot = pd.pivot_table(
        df, index=pivot_index, columns="name", values="point_sum"
    ).ffill()
    pivot = pivot.reindex(  # 並び替え
        target_data["name"].to_list(), axis="columns"
    )
    pivot = pivot.rank(method="dense", ascending=False, axis=1)

    # グラフ生成
    graph_params.update({
        "graph_type": "rank",
        "total_game_count": game_info.count,
        "target_data": target_data,
        "pivot": pivot,
        "horizontal": False,
    })

    match g.adapter.conf.plotting_backend:
        case "plotly":
            graph_params.update({"save_file": "graph.html"})
            save_file = _graph_generation_plotly(graph_params)
        case _:
            graph_params.update({"save_file": "graph.png"})
            save_file = _graph_generation(graph_params)

    file_title = graph_params.get("title_text", "").split()[0]
    m.post.file_list = [{file_title: save_file}]
    m.post.headline = {f"{file_title}グラフ": message.header(game_info, m)}


def _data_collection() -> tuple[pd.DataFrame, pd.DataFrame]:
    """データ収集

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
        - pd.DataFrame: 収集したデータのサマリ
        - pd.DataFrame: 集計範囲のデータ
    """

    # データ収集
    g.params.update(fourfold=True)  # 直近Nは4倍する(縦持ちなので4人分)

    target_data = pd.DataFrame()
    if g.params.get("individual"):  # 個人集計
        df = loader.read_data("SUMMARY_GAMEDATA")
        if df.empty:
            return (target_data, df)

        target_data["name"] = df.groupby("name", as_index=False).last()["name"]
        target_data["last_point"] = df.groupby("name", as_index=False).last()["point_sum"]
        target_data["game_count"] = df.groupby("name", as_index=False).max(numeric_only=True)["count"]

        # 足切り
        target_list = list(
            target_data.query("game_count >= @g.params['stipulated']")["name"]
        )
        _ = target_list  # ignore PEP8 F841
        target_data = target_data.query("name == @target_list").copy()
        df = df.query("name == @target_list").copy()
    else:  # チーム集計
        df = loader.read_data("SUMMARY_GAMEDATA")
        if df.empty:
            return (target_data, df)

        target_data["last_point"] = df.groupby("name").last()["point_sum"]
        target_data["game_count"] = (
            df.groupby("name").max(numeric_only=True)["count"]
        )
        target_data["name"] = target_data.index
        target_data = target_data.sort_values("last_point", ascending=False)

    # 順位付け
    target_data["position"] = target_data["last_point"].rank(ascending=False).astype(int)

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)
        target_data["name"] = target_data["name"].replace(mapping_dict)

    # 凡例用文字列生成
    target_data["legend"] = target_data.apply(
        lambda x: f"{x["position"]}位： {x["name"]} ({x["last_point"]:+.1f}pt / {x["game_count"]:.0f}G)".replace("-", "▲"), axis=1
    )

    return (target_data.sort_values("position"), df)


def _graph_generation(graph_params: GraphParams) -> str:
    """グラフ生成共通処理(matplotlib用)

    Args:
        args (GraphParams): グラフ生成パラメータ

    Returns:
        str: 保存先ファイル名
    """

    save_file = graphutil.setup(graph_params["save_file"])
    target_data = graph_params["target_data"]
    df = graph_params["pivot"]

    if (all(df.count() == 1) or g.params["collection"] == "all") and graph_params["horizontal"]:
        graph_params["graph_type"] = "point_hbar"
        color: list = []
        for _, v in target_data.iterrows():
            if v["last_point"] > 0:
                color.append("deepskyblue")
            else:
                color.append("orangered")

        _graph_title(graph_params)
        tmpdf = pd.DataFrame(
            {"point": target_data["last_point"].to_list()[::-1]},
            index=target_data["legend"].to_list()[::-1],
        )

        tmpdf.plot.barh(
            figsize=(8, 2 + tmpdf.count().iloc[0] / 5),
            y="point",
            xlabel=graph_params["xlabel_text"],
            color=color[::-1],
        ).get_figure()

        plt.legend().remove()
        plt.gca().yaxis.tick_right()

        # X軸修正
        xlocs, xlabs = plt.xticks()
        new_xlabs = [xlab.get_text().replace("−", "▲") for xlab in xlabs]
        plt.xticks(list(xlocs[1:-1]), new_xlabs[1:-1])

        logging.debug("plot data:\n%s", tmpdf)
    else:
        _graph_title(graph_params)
        df.plot(
            figsize=(8, 6),
            xlabel=str(graph_params["xlabel_text"]),
            ylabel=str(graph_params["ylabel_text"]),
            marker="." if len(df) < 20 else None,
            linewidth=2 if len(df) < 40 else 1,
        ).get_figure()

        # 凡例
        plt.legend(
            target_data["legend"].to_list(),
            bbox_to_anchor=(1, 1),
            loc="upper left",
            borderaxespad=0.5,
            ncol=int(len(target_data) / 25 + 1),
        )

        # X軸修正
        plt.xticks(
            list(range(len(df)))[::int(len(df) / 25) + 1],
            list(df.index)[::int(len(df) / 25) + 1],
            rotation=45,
            ha="right",
        )

        # Y軸修正
        ylocs, ylabs = plt.yticks()
        new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
        plt.yticks(list(ylocs[1:-1]), new_ylabs[1:-1])

        logging.debug("plot data:\n%s", df)

    # メモリ調整
    match graph_params["graph_type"]:
        case "point_hbar":
            plt.axvline(x=0, linewidth=0.5, ls="dashed", color="grey")
        case "point":
            plt.axhline(y=0, linewidth=0.5, ls="dashed", color="grey")
        case "rank":
            lab = range(len(target_data) + 1)
            if len(lab) > 10:
                plt.yticks(list(map(int, lab))[1::2], list(map(str, lab))[1::2])
            else:
                plt.yticks(list(map(int, lab))[1:], list(map(str, lab))[1:])
            plt.gca().invert_yaxis()

    plt.title(
        graph_params["title_text"],
        fontsize=16,
    )

    plt.savefig(save_file, bbox_inches="tight")
    return save_file


def _graph_generation_plotly(graph_params: GraphParams) -> str:
    """グラフ生成共通処理(plotly用)

    Args:
        args (GraphParams): グラフ生成パラメータ

    Returns:
        str: 保存先ファイル名
    """

    save_file = graphutil.setup(graph_params["save_file"])
    target_data = cast(pd.DataFrame, graph_params["target_data"])
    df = graph_params["pivot"]

    if (all(df.count() == 1) or g.params["collection"] == "all") and graph_params["horizontal"]:
        graph_params["graph_type"] = "point_hbar"
        df_t = df.T
        df_t.columns = ["point"]
        df_t["rank"] = df_t["point"].rank(ascending=False, method="dense").astype("int")
        df_t["positive"] = df_t["point"] > 0
        fig = px.bar(
            df_t,
            orientation="h",
            color="positive",
            color_discrete_map={True: "blue", False: "red"},
            x=df_t["point"],
            y=target_data["legend"],
        )
    else:
        df.columns = target_data["legend"].to_list()  # 凡例用ラベル生成
        fig = px.line(df, markers=True)

    # グラフレイアウト調整
    _graph_title(graph_params)
    fig.update_layout(
        width=1280,
        height=800,
        title={
            "text": graph_params["title_text"],
            "font": {"size": 30},
            "x": 0.1,
        },
        xaxis_title={
            "text": graph_params["xlabel_text"],
            "font": {"size": 18},
        },
        yaxis_title={
            "text": graph_params["ylabel_text"],
            "font": {"size": 18},
        },
        legend_title=None,
    )

    # 軸/目盛調整
    match graph_params["graph_type"]:
        case "point_hbar":
            fig.update_traces(hovertemplate="%{y}<extra></extra>")
            fig.update_layout(showlegend=False)
            fig.update_yaxes(
                autorange="reversed",
                side="right",
                title=None,
            )
        case "point":
            # マーカー
            if all(df.count() > 20):
                fig.update_traces(mode="lines")
            # ライン
            if len(fig.data) > 40:
                fig.update_traces(mode="lines", line={"width": 1})
        case "rank":
            # Y軸目盛
            lab = list(range(len(target_data) + 1))
            fig.update_yaxes(
                autorange="reversed",
                zeroline=False,
                tickvals=lab[1:] if len(lab) < 10 else lab[1::2],
            )
            # マーカー
            if all(df.count() == 1):
                fig.update_traces(marker={"size": 10})
            elif all(df.count() > 20):
                fig.update_traces(mode="lines")
            # ライン
            if len(fig.data) > 40:
                fig.update_traces(mode="lines", line={"width": 1})

    fig.write_html(save_file, full_html=False)
    return save_file


def _graph_title(graph_params: GraphParams):
    """グラフタイトル生成

    Args:
        args (GraphParams): グラフ生成パラメータ
    """

    if g.params.get("target_count"):
        kind = "ymd_o"
        graph_params.update({"xlabel_text": f"集計日（総ゲーム数：{graph_params["total_game_count"]} ゲーム）"})
        match graph_params.get("graph_type"):
            case "point":
                graph_params.update({"title_text": f"ポイント推移 (直近 {g.params["target_count"]} ゲーム)"})
            case "rank":
                graph_params.update({"title_text": f"順位変動 (直近 {g.params["target_count"]} ゲーム)"})
            case "point_hbar":
                graph_params.update({"title_text": f"通算ポイント (直近 {g.params["target_count"]} ゲーム)"})
    else:
        match g.params.get("collection"):
            case "daily":
                kind = "ymd_o"
                graph_params.update({"xlabel_text": f"集計日（総ゲーム数：{graph_params["total_game_count"]} ゲーム）"})
            case "monthly":
                kind = "jym_o"
                graph_params.update({"xlabel_text": f"集計月（総ゲーム数：{graph_params["total_game_count"]} ゲーム）"})
            case "yearly":
                kind = "jy_o"
                graph_params.update({"xlabel_text": f"集計年（総ゲーム数：{graph_params["total_game_count"]} ゲーム）"})
            case "all":
                kind = "ymdhm"
                graph_params.update({"xlabel_text": f"総ゲーム数：{graph_params["total_game_count"]} ゲーム"})
            case _:
                kind = "ymdhm"
                if g.params.get("search_word"):
                    graph_params.update({"xlabel_text": f"総ゲーム数：{graph_params["total_game_count"]} ゲーム"})
                else:
                    graph_params.update({"xlabel_text": f"ゲーム終了日時（{graph_params["total_game_count"]} ゲーム）"})

    match graph_params.get("graph_type", "point"):
        case "point":
            graph_params.update({
                "ylabel_text": "通算ポイント",
                "title_text": compose.text_item.date_range(kind, "通算ポイント", "ポイント推移"),
            })
        case "rank":
            graph_params.update({
                "ylabel_text": "順位 (通算ポイント順)",
                "title_text": compose.text_item.date_range(kind, "順位", "順位変動"),
            })
        case "point_hbar":
            graph_params.update({
                "ylabel_text": None,
                "xlabel_text": f"通算ポイント（総ゲーム数：{graph_params["total_game_count"]} ゲーム）",
                "title_text": compose.text_item.date_range(kind, "通算ポイント", "通算ポイント"),
            })
