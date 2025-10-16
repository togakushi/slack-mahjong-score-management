"""
libs/commands/graph/personal.py
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from matplotlib import gridspec
from plotly.subplots import make_subplots  # type: ignore

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.types import StyleOptions
from libs.utils import formatter, graphutil, textutil

if TYPE_CHECKING:
    from pathlib import Path

    from integrations.protocols import MessageParserProtocol


def plot(m: "MessageParserProtocol"):
    """個人成績のグラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ収集
    game_info = GameInfo()
    g.params.update(guest_skip=g.params.get("guest_skip2"))
    df = loader.read_data("SUMMARY_GAMEDATA")
    df.index = df.index + 1

    if df.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    player = formatter.name_replace(g.params["player_name"], add_mark=True)
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping([g.params["player_name"]])
        player = next(iter(mapping_dict.values()))

    # 最終値（凡例追加用）
    point_sum = f"{float(df["point_sum"].iloc[-1]):+.1f}".replace("-", "▲")
    point_avg = f"{float(df["point_avg"].iloc[-1]):+.1f}".replace("-", "▲")
    rank_avg = f"{float(df["rank_avg"].iloc[-1]):.2f}"

    title_text = f"『{player}』の成績"
    if g.params.get("target_count", 0) == 0:
        title_range = f"({ExtDt(g.params["starttime"]).format("ymdhm")} - {ExtDt(g.params["endtime"]).format("ymdhm")})"
    else:
        title_range = f"(直近 {len(df)} ゲーム)"

    m.post.headline = {title_text: message.header(game_info, m)}
    m.set_data("", formatter.df_rename(df.drop(columns=["count", "name"]), False), StyleOptions(show_index=True, header_hidden=True))

    # --- グラフ生成
    graphutil.setup()
    match g.adapter.conf.plotting_backend:
        case "plotly":
            m.set_data("通算ポイント", plotly_point(df, title_range))
            m.set_data("獲得順位", plotly_rank(df, title_range))
        case "matplotlib":
            save_file = textutil.save_file_path("graph.png")
            fig = plt.figure(figsize=(12, 8))
            fig.suptitle(f"{title_text} {title_range}", fontsize=16)

            grid = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[3, 1])
            point_ax = fig.add_subplot(grid[0])
            rank_ax = fig.add_subplot(grid[1], sharex=point_ax)

            # ポイント推移
            point_ax.plot(df["playtime"], df["point_sum"], marker="." if len(df) < 50 else None)
            point_ax.plot(df["playtime"], df["point_avg"], marker="." if len(df) < 50 else None)
            df.filter(items=["point"]).plot.bar(
                ax=point_ax,
                color="blue",
            )
            point_ax.legend(
                [f"通算ポイント ({point_sum}pt)", f"平均ポイント ({point_avg}pt)", "獲得ポイント"],
                bbox_to_anchor=(1, 1),
                loc="upper left",
                borderaxespad=0.5,
            )
            point_ax.axhline(y=0, linewidth=0.5, ls="dashed", color="grey")

            ylabs = point_ax.get_yticks()[1:-1]
            point_ax.set_yticks(ylabs)
            point_ax.set_yticklabels(
                [str(int(ylab)).replace("-", "▲") for ylab in ylabs]
            )

            # 獲得順位
            rank_ax.plot(df["playtime"], df["rank"], marker="." if len(df) < 50 else None)
            rank_ax.plot(df["playtime"], df["rank_avg"], marker="." if len(df) < 50 else None)
            rank_ax.set_xlabel(f"ゲーム終了日時（{len(df)} ゲーム）")
            rank_ax.legend(
                ["獲得順位", f"平均順位 ({rank_avg})"],
                bbox_to_anchor=(1, 1),
                loc="upper left",
                borderaxespad=0.5,
            )

            rank_ax.set_xticks(list(df.index)[::int(len(df) / 25) + 1])
            rank_ax.set_xticklabels(
                list(df["playtime"])[::int(len(df) / 25) + 1],
                rotation=45,
                ha="right"
            )
            rank_ax.axhline(y=2.5, linewidth=0.5, ls="dashed", color="grey")
            rank_ax.invert_yaxis()

            fig.tight_layout()
            plt.savefig(save_file, bbox_inches="tight")

            m.set_data(
                f"『{player}』の成績", save_file,
                StyleOptions(use_comment=True, header_hidden=True, key_title=False)
            )


def statistics_plot(m: "MessageParserProtocol"):
    """個人成績の統計グラフを生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ収集
    game_info = GameInfo()
    g.params.update(guest_skip=g.params.get("guest_skip2"))
    df = loader.read_data("SUMMARY_DETAILS")

    if df.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    if g.params.get("individual"):  # 個人成績
        player = formatter.name_replace(g.params["player_name"], add_mark=True)
    else:  # チーム成績
        player = g.params["player_name"]

    df = df.filter(items=["playtime", "name", "rpoint", "rank", "point"])
    df["rpoint"] = df["rpoint"] * 100

    player_df = df.query("name == @player").reset_index(drop=True)

    if player_df.empty:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    player_df["sum_point"] = player_df["point"].cumsum()

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping([g.params["player_name"]])
        player = next(iter(mapping_dict.values()))

    title_text = f"『{player}』の成績 (検索範囲：{compose.text_item.date_range("ymd_o")})"

    rpoint_df = get_data(player_df["rpoint"], g.params["interval"])
    point_sum_df = get_data(player_df["point"], g.params["interval"])
    point_df = get_data(player_df["sum_point"], g.params["interval"]).iloc[-1]
    rank_df = get_data(player_df["rank"], g.params["interval"])
    total_index = "全区間"

    rpoint_stats = {
        "ゲーム数": rpoint_df.count().astype("int"),
        "平均値(x)": rpoint_df.mean().round(1),
        "最小値": rpoint_df.min().astype("int"),
        "第一四分位数": rpoint_df.quantile(0.25).astype("int"),
        "中央値(|)": rpoint_df.median().astype("int"),
        "第三四分位数": rpoint_df.quantile(0.75).astype("int"),
        "最大値": rpoint_df.max().astype("int"),
    }

    stats_df = pd.DataFrame(rpoint_stats)
    stats_df.loc[total_index] = pd.Series(
        {
            "ゲーム数": int(player_df["rpoint"].count()),
            "平均値(x)": float(round(player_df["rpoint"].mean(), 1)),
            "最小値": int(player_df["rpoint"].min()),
            "第一四分位数": int(player_df["rpoint"].quantile(0.25)),
            "中央値(|)": int(player_df["rpoint"].median()),
            "第三四分位数": int(player_df["rpoint"].quantile(0.75)),
            "最大値": int(player_df["rpoint"].max()),
        }
    )
    stats_df = stats_df.apply(lambda col: col.map(lambda x: f"{int(x)}" if isinstance(x, int) else f"{x:.1f}"))

    count_stats = {
        "ゲーム数": rank_df.count().astype("int"),
        "1位": rank_df[rank_df == 1].count().astype("int"),
        "1位(%)": ((rank_df[rank_df == 1].count()) / rank_df.count()),
        "2位": rank_df[rank_df == 2].count().astype("int"),
        "2位(%)": ((rank_df[rank_df == 2].count()) / rank_df.count()),
        "3位": rank_df[rank_df == 3].count().astype("int"),
        "3位(%)": ((rank_df[rank_df == 3].count()) / rank_df.count()),
        "4位": rank_df[rank_df == 4].count().astype("int"),
        "4位(%)": ((rank_df[rank_df == 4].count()) / rank_df.count()),
        "平均順位": rank_df.mean().round(2),
        "区間ポイント": point_sum_df.sum().round(1),
        "区間平均": point_sum_df.mean().round(1),
        "通算ポイント": point_df.round(1),
    }
    count_df = pd.DataFrame(count_stats)

    count_df.loc[total_index] = pd.Series(
        {
            "ゲーム数": int(count_df["ゲーム数"].sum()),
            "1位": int(count_df["1位"].sum()),
            "1位(%)": float(count_df["1位"].sum() / count_df["ゲーム数"].sum()),
            "2位": int(count_df["2位"].sum()),
            "2位(%)": float(count_df["2位"].sum() / count_df["ゲーム数"].sum()),
            "3位": int(count_df["3位"].sum()),
            "3位(%)": float(count_df["3位"].sum() / count_df["ゲーム数"].sum()),
            "4位": int(count_df["4位"].sum()),
            "4位(%)": float(count_df["4位"].sum() / count_df["ゲーム数"].sum()),
            "平均順位": float(round(player_df["rank"].mean(), 2)),
            "区間ポイント": float(round(player_df["point"].sum(), 1)),
            "区間平均": float(round(player_df["point"].mean(), 1)),
        }
    )
    # テーブル用データ
    rank_table = pd.DataFrame()
    rank_table["ゲーム数"] = count_df["ゲーム数"].astype("int")
    rank_table["1位"] = count_df.apply(lambda row: f"{row["1位(%)"]:.2%} ({row["1位"]:.0f})", axis=1)
    rank_table["2位"] = count_df.apply(lambda row: f"{row["2位(%)"]:.2%} ({row["2位"]:.0f})", axis=1)
    rank_table["3位"] = count_df.apply(lambda row: f"{row["3位(%)"]:.2%} ({row["3位"]:.0f})", axis=1)
    rank_table["4位"] = count_df.apply(lambda row: f"{row["4位(%)"]:.2%} ({row["4位"]:.0f})", axis=1)
    rank_table["平均順位"] = count_df.apply(lambda row: f"{row["平均順位"]:.2f}", axis=1)

    m.post.headline = {f"『{player}』の成績": message.header(game_info, m)}

    # --- グラフ生成
    graphutil.setup()
    match g.adapter.conf.plotting_backend:
        case "plotly":
            m.set_data("順位/ポイント情報", count_df, StyleOptions(show_index=True))
            m.set_data("通算ポイント", plotly_line("通算ポイント推移", point_df))
            m.set_data("順位分布", plotly_bar("順位分布", count_df.drop(index=["全区間"])))
            m.set_data("素点情報", stats_df, StyleOptions(show_index=True))
            m.set_data("素点分布", plotly_box("素点分布", rpoint_df))
        case "matplotlib":
            fig = plt.figure(figsize=(20, 10))
            fig.suptitle(title_text, size=20, weight="bold")
            gs = gridspec.GridSpec(figure=fig, nrows=3, ncols=2)

            ax_point1 = fig.add_subplot(gs[0, 0])
            ax_point2 = fig.add_subplot(gs[0, 1])
            ax_rank1 = fig.add_subplot(gs[1, 0])
            ax_rank2 = fig.add_subplot(gs[1, 1])
            ax_rpoint1 = fig.add_subplot(gs[2, 0])
            ax_rpoint2 = fig.add_subplot(gs[2, 1])

            plt.subplots_adjust(wspace=0.22, hspace=0.18)

            # ポイントデータ
            subplot_point(point_df, ax_point1)
            subplot_table(count_df.filter(items=["ゲーム数", "区間ポイント", "区間平均", "通算ポイント"]), ax_point2)

            # 順位データ
            subplot_rank(count_df.copy(), ax_rank1, total_index)
            subplot_table(rank_table, ax_rank2)

            # 素点データ
            subplot_box(rpoint_df, ax_rpoint1)
            subplot_table(stats_df, ax_rpoint2)

            save_file = textutil.save_file_path("graph.png")
            plt.savefig(save_file, bbox_inches="tight")

            m.set_data("個人成績", save_file, StyleOptions(use_comment=True, header_hidden=True))


def get_data(df: pd.Series, interval: int) -> pd.DataFrame:
    """データフレームを指定範囲で分割する

    Args:
        df (pd.Series): 分割するデータ
        interval (int): 1ブロックに収めるデータ数

    Returns:
        pd.DataFrame: 分割されたデータ
    """

    # interval単位で分割
    rpoint_data: dict = {}

    fraction = 0 if not len(df) % interval else interval - len(df) % interval  # 端数
    if fraction:
        df = pd.concat([pd.Series([None] * fraction), df], ignore_index=True)

    for x in range(int(len(df) / interval)):
        s = len(df) % interval + interval * x
        e = s + interval
        rpoint_data[f"{max(1, s + 1 - fraction):3d}G - {(e - fraction):3d}G"] = df.iloc[s:e].tolist()

    return pd.DataFrame(rpoint_data)


def subplot_box(df: pd.DataFrame, ax: plt.Axes) -> None:
    """箱ひげ図を生成する

    Args:
        df (pd.DataFrame): プロットデータ
        ax (plt.Axes): プロット先オブジェクト
    """

    p = [x + 1 for x in range(len(df.columns))]
    df.plot(
        ax=ax,
        kind="box",
        title="素点分布",
        showmeans=True,
        meanprops={"marker": "x", "markeredgecolor": "b", "markerfacecolor": "b", "ms": 3},
        flierprops={"marker": ".", "markeredgecolor": "r"},
        ylabel="素点(点)",
        sharex=True,
    )
    ax.axhline(y=25000, linewidth=0.5, ls="dashed", color="grey")
    ax.set_xticks(p)
    ax.set_xticklabels(df.columns, rotation=45, ha="right")

    # Y軸修正
    ylabs = ax.get_yticks()[1:-1]
    ax.set_yticks(ylabs)
    ax.set_yticklabels(
        [str(int(ylab)).replace("-", "▲") for ylab in ylabs]
    )


def subplot_table(df: pd.DataFrame, ax: plt.Axes) -> None:
    """テーブルを生成する

    Args:
        df (pd.DataFrame): プロットデータ
        ax (plt.Axes): プロット先オブジェクト
    """

    # 有効桁数の調整
    for col in df.columns:
        match col:
            case "ゲーム数":
                df[col] = df[col].apply(lambda x: int(float(x)))
            case "区間ポイント" | "区間平均" | "通算ポイント":
                df[col] = df[col].apply(lambda x: f"{float(x):+.1f}")
            case "平均順位":
                df[col] = df[col].apply(lambda x: f"{float(x):.2f}")
            case "平均値(x)":
                df[col] = df[col].apply(lambda x: f"{float(x):.1f}")
            case "最小値" | "第一四分位数" | "中央値(|)" | "第三四分位数" | "最大値":
                df[col] = df[col].apply(lambda x: int(float(x)))

    df = df.apply(lambda col: col.map(lambda x: str(x).replace("-", "▲")))
    df.replace("+nan", "-----", inplace=True)

    table = ax.table(
        cellText=df.values.tolist(),
        colLabels=df.columns.tolist(),
        rowLabels=df.index.tolist(),
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    ax.axis("off")


def subplot_point(df: pd.Series, ax: plt.Axes) -> None:
    """ポイントデータ

    Args:
        df (pd.Series): プロットデータ
        ax (plt.Axes): プロット先オブジェクト
    """

    df.plot(  # レイアウト調整用ダミー
        ax=ax,
        kind="bar",
        alpha=0,
    )
    df.plot(
        ax=ax,
        kind="line",
        title="ポイント推移",
        ylabel="通算ポイント(pt)",
        marker="o",
        color="b",
    )
    # Y軸修正
    ylabs = ax.get_yticks()[1:-1]
    ax.set_yticks(ylabs)
    ax.set_yticklabels(
        [str(int(ylab)).replace("-", "▲") for ylab in ylabs]
    )


def subplot_rank(df: pd.DataFrame, ax: plt.Axes, total_index: str) -> None:
    """順位データ

    Args:
        df (pd.DataFrame): プロットデータ
        ax (plt.Axes): プロット先オブジェクト
        total_index (str): 合計値格納index
    """

    df["1位(%)"] = df["1位(%)"] * 100
    df["2位(%)"] = df["2位(%)"] * 100
    df["3位(%)"] = df["3位(%)"] * 100
    df["4位(%)"] = df["4位(%)"] * 100

    ax_rank_avg = ax.twinx()
    df.filter(items=["平均順位"]).drop(index=total_index).plot(
        ax=ax_rank_avg,
        kind="line",
        ylabel="平均順位",
        yticks=[1, 2, 3, 4],
        ylim=[0.85, 4.15],
        marker="o",
        color="b",
        legend=False,
        grid=False,
    )
    ax_rank_avg.invert_yaxis()
    ax_rank_avg.axhline(y=2.5, linewidth=0.5, ls="dashed", color="grey")

    filter_items = ["1位(%)", "2位(%)", "3位(%)", "4位(%)"]
    df.filter(items=filter_items).drop(index=total_index).plot(
        ax=ax,
        kind="bar",
        title="獲得順位",
        ylabel="獲得順位(%)",
        colormap="Set2",
        stacked=True,
        rot=90,
        ylim=[-5, 105],
    )
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax_rank_avg.get_legend_handles_labels()
    ax.legend(
        h1 + h2,
        l1 + l2,
        bbox_to_anchor=(0.5, 0),
        loc="lower center",
        ncol=5,
    )


def plotly_point(df: pd.DataFrame, title_range: str) -> "Path":
    """獲得ポイントグラフ(plotly用)

    Args:
        df (pd.DataFrame): プロットするデータ
        title_range (str): 集計範囲(タイトル用)

    Returns:
        Path: 保存先ファイルパス
    """

    save_file = textutil.save_file_path("point.html")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name="通算ポイント",
            zorder=2,
            mode="lines",
            x=df["playtime"],
            y=df["point_sum"],
        ),
    )
    fig.add_trace(
        go.Bar(
            name="獲得ポイント",
            zorder=1,
            x=df["playtime"],
            y=df["point"],
            marker_color=["darkgreen" if v >= 0 else "firebrick" for v in df["point"]],
        ),
    )

    fig.update_layout(
        barmode="overlay",
        title={
            "text": f"通算ポイント {title_range}",
            "font": {"size": 30},
            "xref": "paper",
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis_title={
            "text": f"ゲーム終了日時（{len(df)} ゲーム）",
            "font": {"size": 18},
        },
        legend_title=None,
    )

    fig.update_yaxes(
        title={
            "text": "ポイント(pt)",
            "font": {"size": 18, "color": "white"},
        },
    )

    fig.write_html(save_file, full_html=False)
    return save_file


def plotly_rank(df: pd.DataFrame, title_range: str) -> "Path":
    """獲得順位グラフ(plotly用)

    Args:
        df (pd.DataFrame): プロットするデータ
        title_range (str): 集計範囲(タイトル用)

    Returns:
        Path: 保存先ファイルパス
    """

    save_file = textutil.save_file_path("rank.html")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name="獲得順位",
            zorder=1,
            mode="lines",
            x=df["playtime"],
            y=df["rank"],
        ),
    )
    fig.add_trace(
        go.Scatter(
            name="平均順位",
            zorder=2,
            mode="lines",
            x=df["playtime"],
            y=df["rank_avg"],
            line={"width": 5},
        ),
    )

    fig.update_layout(
        title={
            "text": f"獲得順位 {title_range}",
            "font": {"size": 30},
            "xref": "paper",
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis_title={
            "text": f"ゲーム終了日時（{len(df)} ゲーム）",
            "font": {"size": 18},
        },
        legend_title=None,
    )

    fig.update_yaxes(
        title={
            "text": "順位",
            "font": {"size": 18, "color": "white"},
        },
        range=[4.2, 0.8],
        tickvals=[4, 3, 2, 1],
        zeroline=False,
    )

    fig.add_hline(
        y=2.5,
        line_dash="dot",
        line_color="white",
        line_width=2,
        layer="below",
    )

    fig.write_html(save_file, full_html=False)
    return save_file


def plotly_line(title_text: str, df: pd.Series) -> "Path":
    """通算ポイント推移グラフ生成(plotly用)

    Args:
        title_text (str): グラフタイトル
        df (pd.DataFrame): プロットするデータ

    Returns:
        Path: 保存先ファイルパス
    """

    save_file = textutil.save_file_path("point.html")

    fig = go.Figure()
    fig.add_traces(
        go.Scatter(
            mode="lines+markers",
            x=df.index,
            y=df.values,
        ),
    )

    fig.update_layout(
        title={
            "text": title_text,
            "font": {"size": 30},
            "xref": "paper",
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis_title={
            "text": "ゲーム区間",
            "font": {"size": 18},
        },
        yaxis_title={
            "text": "ポイント（pt）",
            "font": {"size": 18},
        },
        showlegend=False,
    )
    fig.update_yaxes(
        tickformat="d",
    )

    fig.write_html(save_file, full_html=False)
    return save_file


def plotly_box(title_text: str, df: pd.DataFrame) -> "Path":
    """素点分布グラフ生成(plotly用)

    Args:
        title_text (str): グラフタイトル
        df (pd.DataFrame): プロットするデータ

    Returns:
        Path: 保存先ファイルパス
    """

    save_file = textutil.save_file_path("rpoint.html")
    fig = px.box(df)
    fig.update_layout(
        title={
            "text": title_text,
            "font": {"size": 30},
            "xref": "paper",
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis_title={
            "text": "ゲーム区間",
            "font": {"size": 18},
        },
        yaxis_title={
            "text": "素点（点）",
            "font": {"size": 18},
        },
    )
    fig.update_yaxes(
        zeroline=False,
        tickformat="d",
    )
    fig.add_hline(
        y=25000,
        line_dash="dot",
        line_color="white",
        line_width=1,
        layer="below",
    )

    fig.write_html(save_file, full_html=False)
    return save_file


def plotly_bar(title_text: str, df: pd.DataFrame) -> "Path":
    """順位分布グラフ生成(plotly用)

    Args:
        title_text (str): グラフタイトル
        df (pd.Series): プロットするデータ

    Returns:
        Path: 保存先ファイルパス
    """

    save_file = textutil.save_file_path("rank.html")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # 獲得率
    fig.add_trace(go.Bar(name="4位率", x=df.index, y=df["4位(%)"] * 100), secondary_y=False)
    fig.add_trace(go.Bar(name="3位率", x=df.index, y=df["3位(%)"] * 100), secondary_y=False)
    fig.add_trace(go.Bar(name="2位率", x=df.index, y=df["2位(%)"] * 100), secondary_y=False)
    fig.add_trace(go.Bar(name="1位率", x=df.index, y=df["1位(%)"] * 100), secondary_y=False)
    # 平均順位
    fig.add_trace(
        go.Scatter(
            mode="lines+markers",
            name="平均順位",
            x=df.index,
            y=df["平均順位"],
        ),
        secondary_y=True,
    )

    fig.update_layout(
        barmode="stack",
        title={
            "text": title_text,
            "font": {"size": 30},
            "xref": "paper",
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis_title={
            "text": "ゲーム区間",
            "font": {"size": 18},
        },
        legend_traceorder="reversed",
        legend_title=None,
        legend={
            "xanchor": "center",
            "yanchor": "bottom",
            "orientation": "h",
            "x": 0.5,
            "y": 0.02,
        },
    )
    fig.update_yaxes(  # Y軸(左)
        title={
            "text": "獲得順位（％）",
            "font": {"size": 18, "color": "white"},
        },
        secondary_y=False,
        zeroline=False,
    )
    fig.update_yaxes(  # Y軸(右)
        secondary_y=True,
        title={
            "text": "平均順位",
            "font": {"size": 18, "color": "white"},
        },
        tickfont_color="white",
        range=[4, 1],
        showgrid=False,
        zeroline=False,
    )

    fig.write_html(save_file, full_html=False)
    return save_file
