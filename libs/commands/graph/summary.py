"""
libs/commands/graph/summary.py
"""

import logging
import os
from typing import TYPE_CHECKING, TypeVar

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px  # type: ignore

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict
from integrations.protocols import MessageParserProtocol
from libs.data import aggregate, loader
from libs.functions import compose, configuration, message
from libs.utils import formatter, textutil

if TYPE_CHECKING:
    from integrations.base.interface import IntegrationsConfig

AppConfig = TypeVar("AppConfig", bound="IntegrationsConfig")


def point_plot(m: MessageParserProtocol[AppConfig]) -> bool:
    """ポイント推移グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 初期化
    title_text = None
    xlabel_text = None

    # 保存ファイル名
    match pd.options.plotting.backend:
        case "plotly":
            save_file = textutil.save_file_path(".html")
        case _:
            save_file = textutil.save_file_path(".png")

    if os.path.exists(save_file):
        os.remove(save_file)

    # データ収集
    game_info: GameInfoDict = aggregate.game_info()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        return False

    # グラフタイトル/X軸ラベル
    pivot_index = "playtime"
    if g.params.get("target_count"):
        title_text = f"ポイント推移 (直近 {g.params["target_count"]} ゲーム)"
        xlabel_text = f"集計日（総ゲーム数：{game_info["game_count"]} ゲーム）"
    else:
        match g.params["collection"]:
            case "daily":
                xlabel_text = f"集計日（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("ymd_o", "通算ポイント", "ポイント推移")
            case "monthly":
                xlabel_text = f"集計月（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("jym_o", "通算ポイント", "ポイント推移")
            case "yearly":
                xlabel_text = f"集計年（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("jy_o", "通算ポイント", "ポイント推移")
            case "all":
                xlabel_text = f"総ゲーム数：{game_info["game_count"]} ゲーム"
                title_text = compose.text_item.date_range("ymdhm", "通算ポイント", "ポイント推移")
            case _:
                if g.params.get("search_word"):
                    pivot_index = "comment"
                    xlabel_text = f"（総ゲーム数：{game_info["game_count"]} ゲーム）"
                    if game_info["first_comment"] == game_info["last_comment"]:
                        title_text = f"通算ポイント ({game_info["first_comment"]})"
                    else:
                        title_text = f"ポイント推移 ({game_info["first_comment"]} - {game_info["last_comment"]})"
                else:
                    xlabel_text = f"ゲーム終了日時（{game_info["game_count"]} ゲーム）"
                    title_text = compose.text_item.date_range("ymdhm", "通算ポイント", "ポイント推移")
                    if ExtDt(g.params["starttime"]).format("ymd") == ExtDt(g.params["onday"]).format("ymd") and game_info["game_count"] == 1:
                        title_text = f"獲得ポイント ({ExtDt(g.params["starttime"]).format("ymd")})"

    # 集計
    pivot = pd.pivot_table(
        df, index=pivot_index, columns="name", values="point_sum"
    ).ffill()
    pivot = pivot.reindex(  # 並び替え
        target_data["name"].to_list(), axis="columns"
    )

    # グラフ生成
    args = {
        "kind": "point",
        "title_text": title_text,
        "total_game_count": game_info["game_count"],
        "target_data": target_data,
        "legend": "name",
        "xlabel_text": xlabel_text,
        "ylabel_text": "通算ポイント",
        "horizontal": True,
    }

    match pd.options.plotting.backend:
        case "plotly":
            fig = _graph_generation_plotly(pivot, **args)
            fig.write_html(save_file)
        case _:
            fig = _graph_generation(pivot, **args)
            plt.savefig(save_file, bbox_inches="tight")

    m.post.file_list = [{"ポイント推移": save_file}]
    return True


def rank_plot(m: MessageParserProtocol[AppConfig]) -> bool:
    """順位変動グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 初期化
    title_text = None
    xlabel_text = None

    # データ収集
    game_info: GameInfoDict = aggregate.game_info()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        m.post.headline = {"0": message.random_reply(m, "no_hits", False)}
        return False

    # グラフタイトル/X軸ラベル
    pivot_index = "playtime"
    if g.params.get("target_count"):
        title_text = f"順位変動 (直近 {g.params["target_count"]} ゲーム)"
        xlabel_text = f"集計日（総ゲーム数：{game_info["game_count"]} ゲーム）"
    else:
        match g.params["collection"]:
            case "daily":
                xlabel_text = f"集計日（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("ymd_o", "順位", "順位変動")
            case "monthly":
                xlabel_text = f"集計月（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("jym", "順位", "順位変動")
            case "yearly":
                xlabel_text = f"集計年（総ゲーム数：{game_info["game_count"]} ゲーム）"
                title_text = compose.text_item.date_range("jy", "順位", "順位変動")
            case "all":
                xlabel_text = f"総ゲーム数：{game_info["game_count"]} ゲーム"
                title_text = compose.text_item.date_range("ymdhm", "順位", "順位変動")
            case _:
                if g.params.get("search_word"):
                    pivot_index = "comment"
                    xlabel_text = f"（総ゲーム数：{game_info["game_count"]} ゲーム）"
                    if game_info["first_comment"] == game_info["last_comment"]:
                        title_text = f"順位 ({game_info["first_comment"]})"
                    else:
                        title_text = f"順位変動 ({game_info["first_comment"]} - {game_info["last_comment"]})"
                else:
                    xlabel_text = f"ゲーム終了日時（{game_info["game_count"]} ゲーム）"
                    title_text = compose.text_item.date_range("ymdhm", "順位", "順位変動")
                    if ExtDt(g.params["starttime"]).format("ymd") == ExtDt(g.params["onday"]).format("ymd") and game_info["game_count"] == 1:
                        title_text = f"順位 ({ExtDt(g.params["starttime"]).format("ymd")})"

    # 集計
    pivot = pd.pivot_table(
        df, index=pivot_index, columns="name", values="point_sum"
    ).ffill()
    pivot = pivot.reindex(  # 並び替え
        target_data["name"].to_list(), axis="columns"
    )
    pivot = pivot.rank(method="dense", ascending=False, axis=1)

    # グラフ生成
    args = {
        "kind": "rank",
        "title_text": title_text,
        "total_game_count": game_info["game_count"],
        "target_data": target_data,
        "legend": "name",
        "xlabel_text": xlabel_text,
        "ylabel_text": "順位 (通算ポイント順)",
        "horizontal": False,
    }

    match pd.options.plotting.backend:
        case "plotly":
            save_file = textutil.save_file_path(".html")
            fig = _graph_generation_plotly(pivot, **args)
            fig.update_layout(yaxis={"autorange": "reversed"})
            fig.write_html(save_file, full_html=False)
        case _:
            save_file = textutil.save_file_path(".png")
            fig = _graph_generation(pivot, **args)
            plt.savefig(save_file, bbox_inches="tight")

    m.post.file_list = [{"順位変動": save_file}]
    return True


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
        df = loader.read_data("summary/gamedata.sql")
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
        df = loader.read_data("summary/gamedata.sql")
        if df.empty:
            return (target_data, df)

        target_data["last_point"] = df.groupby("name").last()["point_sum"]
        target_data["game_count"] = (
            df.groupby("name").max(numeric_only=True)["count"]
        )
        target_data["name"] = target_data.index
        target_data = target_data.sort_values("last_point", ascending=False)

    # 順位付け
    target_data["position"] = (
        target_data["last_point"].rank(ascending=False).astype(int)
    )

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)
        target_data["name"] = target_data["name"].replace(mapping_dict)

    return (target_data.sort_values("position"), df)


def _graph_generation(df: pd.DataFrame, **kwargs):
    """グラフ生成共通処理

    Args:
        df (pd.DataFrame): グラフ描写データ
        kwargs (dict): グラフ生成パラメータ

    """

    configuration.graph_setup()

    if (all(df.count() == 1) or g.params["collection"] == "all") and kwargs["horizontal"]:
        kwargs["kind"] = "barh"
        lab: list = []
        color: list = []
        for _, v in kwargs["target_data"].iterrows():
            lab.append("{:2d}位：{} ({}pt / {}G)".format(  # pylint: disable=consider-using-f-string
                v["position"],
                v[kwargs["legend"]],
                "{:+.1f}".format(v["last_point"]).replace("-", "▲"),  # pylint: disable=consider-using-f-string
                v["game_count"],
            ))
            if v["last_point"] > 0:
                color.append("deepskyblue")
            else:
                color.append("orangered")

        tmpdf = pd.DataFrame(
            {"point": kwargs["target_data"]["last_point"].to_list()[::-1]},
            index=lab[::-1],
        )

        fig = tmpdf.plot.barh(
            figsize=(8, 2 + tmpdf.count().iloc[0] / 5),
            y="point",
            xlabel=f"総ゲーム数：{kwargs["total_game_count"]} ゲーム",
            color=color[::-1],
        ).get_figure()

        plt.legend().remove()
        plt.gca().yaxis.tick_right()

        # X軸修正
        xlocs, xlabs = plt.xticks()
        new_xlabs = [xlab.get_text().replace("−", "▲") for xlab in xlabs]
        plt.xticks(list(xlocs[1:-1]), new_xlabs[1:-1])

        logging.info("plot data:\n%s", tmpdf)
    else:
        fig = df.plot(
            figsize=(8, 6),
            xlabel=kwargs["xlabel_text"],
            ylabel=kwargs["ylabel_text"],
            marker="." if len(df) < 50 else None,
        ).get_figure()

        # 凡例
        legend_text = []
        for _, v in kwargs["target_data"].iterrows():
            legend_text.append("{:2d}位：{} ({}pt / {}G)".format(  # pylint: disable=consider-using-f-string
                v["position"], v[kwargs["legend"]],
                "{:+.1f}".format(v["last_point"]).replace("-", "▲"),  # pylint: disable=consider-using-f-string
                v["game_count"],
            ))

        plt.legend(
            legend_text,
            bbox_to_anchor=(1, 1),
            loc="upper left",
            borderaxespad=0.5,
            ncol=int(len(kwargs["target_data"]) / 25 + 1),
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

        logging.info("plot data:\n%s", df)

    #
    match kwargs["kind"]:
        case "barh":
            plt.axvline(x=0, linewidth=0.5, ls="dashed", color="grey")
        case "point":
            plt.axhline(y=0, linewidth=0.5, ls="dashed", color="grey")
        case "rank":
            lab = list(range(len(kwargs["target_data"]) + 1))
            if len(lab) > 10:
                plt.yticks(lab[1::2], lab[1::2])
            else:
                plt.yticks(lab[1:], lab[1:])
            plt.gca().invert_yaxis()

    plt.title(
        kwargs["title_text"],
        fontsize=16,
    )

    return fig


def _graph_generation_plotly(df: pd.DataFrame, **kwargs):
    """グラフ生成共通処理

    Args:
        df (pd.DataFrame): グラフ描写データ
        kwargs (dict): グラフ生成パラメータ

    """

    if (all(df.count() == 1) or g.params["collection"] == "all") and kwargs["horizontal"]:
        df_t = df.T
        df_t.columns = ["point"]
        df_t["rank"] = df_t["point"].rank(ascending=False, method="dense").astype("int")
        df_t["positive"] = df_t["point"] > 0
        df_t["label"] = df_t.apply(lambda x: f"{x["rank"]:3d}位：{x.name} ({x["point"]:+.1f} pt)", axis=1)

        fig = px.bar(
            df_t,
            orientation="h",
            color="positive",
            color_discrete_map={True: "blue", False: "red"},
            x=df_t["point"],
            y=df_t["label"],
        )
        fig.update_traces(
            hovertemplate="%{y}<extra></extra>"
        )
        fig.update_layout(
            xaxis={
                "title": {"text": f"獲得ポイント (総ゲーム数：{kwargs["total_game_count"]} ゲーム)"}
            },
            yaxis={
                "autorange": "reversed",
                "side": "right",
                "title": None,
            },
            showlegend=False,
        )
    else:
        # 凡例用ラベル生成
        work_df = pd.DataFrame()
        if kwargs.get("kind") == "point":
            work_df["last"] = df.tail(1).T
            work_df["rank"] = work_df["last"].rank(ascending=False, method="dense")
            work_df["label"] = work_df.apply(lambda x: f"{x["rank"]:3.0f}位：{x.name} ({x["last"]:+.1f} pt)", axis=1)
        else:
            work_df["rank"] = df.tail(1).T.rank(ascending=True, method="dense")
            work_df["label"] = work_df.apply(lambda x: f"{x["rank"]:3.0f}位：{x.name}", axis=1)
        df.columns = work_df["label"].to_list()

        fig = px.line(df)
        fig.update_layout(
            xaxis={
                "title": {"text": kwargs["xlabel_text"]}
            },
            yaxis={
                "title": {"text": kwargs["ylabel_text"]}
            },
            legend={"title": "プレイヤー名"}
        )

    fig.update_layout(
        width=1280,
        height=800,
        title={
            "text": kwargs["title_text"],
            "x": 0.5,
            "font": {"size": 32},
        }
    )

    return fig
