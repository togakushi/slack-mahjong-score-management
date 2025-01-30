import logging
import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import gridspec

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)


def plot():
    """
    個人成績のグラフを生成する

    Returns
    -------
    game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    plt.close()
    # データ収集
    g.opt.guest_skip = g.opt.guest_skip2
    df = d.aggregate.personal_gamedata()
    player = c.member.name_replace(g.prm.player_name, add_mark=True)

    if df.empty:
        return (0, f.message.reply(message="no_hits"))

    # 最終値（凡例追加用）
    point_sum = "{:+.1f}".format(
        float(df["point_sum"].iloc[-1])
    ).replace("-", "▲")
    point_avg = "{:+.1f}".format(
        float(df["point_avg"].iloc[-1])
    ).replace("-", "▲")
    rank_avg = "{:.2f}".format(float(df["rank_avg"].iloc[-1]))

    # --- グラフ生成
    save_file = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "graph.png",
    )

    f.common.graph_setup(plt, fm)

    fig = plt.figure(figsize=(12, 8))

    if g.prm.target_count == 0:
        title_text = "『{}』の成績 ({} - {})".format(
            player, g.prm.starttime_hm, g.prm.endtime_hm
        )
    else:
        title_text = "『{}』の成績 (直近 {} ゲーム)".format(
            player, len(df)
        )

    grid = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[3, 1])
    point_ax = fig.add_subplot(grid[0])
    rank_ax = fig.add_subplot(grid[1], sharex=point_ax)

    # ---
    df.filter(items=["point_sum", "point_avg"]).plot.line(
        ax=point_ax,
        ylabel="ポイント(pt)",
        marker="." if len(df) < 50 else None,
    )
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

    # Y軸修正
    ylabs = point_ax.get_yticks()[1:-1]
    point_ax.set_yticks(ylabs)
    point_ax.set_yticklabels(
        [str(int(ylab)).replace("-", "▲") for ylab in ylabs]
    )

    # ---
    df.filter(items=["rank", "rank_avg"]).plot.line(
        ax=rank_ax,
        marker="." if len(df) < 50 else None,
        yticks=[1, 2, 3, 4],
        ylabel="順位",
        xlabel=f"ゲーム終了日時（{len(df)} ゲーム）",
    )
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

    fig.suptitle(title_text, fontsize=16)
    fig.tight_layout()
    plt.savefig(save_file, bbox_inches="tight")

    return (len(df), save_file)


def statistics_plot():
    """
    個人成績の統計グラフを生成する

    Returns
    -------
    game_count : int
        集計対象のゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    plt.close()
    # データ収集
    g.opt.guest_skip = g.opt.guest_skip2
    df = d.aggregate.game_details()

    if df.empty:
        return (0, f.message.reply(message="no_hits"))

    df = df.filter(items=["playtime", "name", "rpoint", "rank", "point"])
    df["rpoint"] = df["rpoint"] * 100

    player = c.member.name_replace(g.prm.player_name, add_mark=True)
    player_df = df.query("name == @player").reset_index(drop=True)
    player_df["sum_point"] = player_df["point"].cumsum()

    # --- グラフ生成
    save_file = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "graph.png",
    )
    title_text = "『{}』の成績 (集計期間： {} - {})".format(
        player, g.prm.starttime_ymd, g.prm.endtime_ymd
    )

    rpoint_df = get_data(player_df["rpoint"], g.opt.interval)
    point_sum_df = get_data(player_df["point"], g.opt.interval)
    point_df = get_data(player_df["sum_point"], g.opt.interval).iloc[-1]
    rank_df = get_data(player_df["rank"], g.opt.interval)
    total_index = "全区間"

    rpoint_stats = {
        "ゲーム数": rpoint_df.count(),
        "平均値(x)": rpoint_df.mean().round(1),
        "最小値": rpoint_df.min().astype("int"),
        "第一四分位数": rpoint_df.quantile(0.25).astype("int"),
        "中央値(|)": rpoint_df.median().astype("int"),
        "第三四分位数": rpoint_df.quantile(0.75).astype("int"),
        "最大値": rpoint_df.max().astype("int"),
    }
    stats_df = pd.DataFrame(rpoint_stats)
    stats_df.loc[total_index] = {
        "ゲーム数": player_df["rpoint"].count(),
        "平均値(x)": player_df["rpoint"].mean().round(1),
        "最小値": player_df["rpoint"].min().astype("int"),
        "第一四分位数": player_df["rpoint"].quantile(0.25).astype("int"),
        "中央値(|)": player_df["rpoint"].median().astype("int"),
        "第三四分位数": player_df["rpoint"].quantile(0.75).astype("int"),
        "最大値": player_df["rpoint"].max().astype("int"),
    }
    stats_df = stats_df.apply(lambda col: col.map(lambda x: f"{int(x)}" if isinstance(x, int) else f"{x:.1f}"))

    count_stats = {
        "ゲーム数": rank_df.count().astype("int"),
        "1位": rank_df[rank_df == 1].count().astype("int"),
        "2位": rank_df[rank_df == 2].count().astype("int"),
        "3位": rank_df[rank_df == 3].count().astype("int"),
        "4位": rank_df[rank_df == 4].count().astype("int"),
        "1位(%)": ((rank_df[rank_df == 1].count()) / rank_df.count() * 100).round(2),
        "2位(%)": ((rank_df[rank_df == 2].count()) / rank_df.count() * 100).round(2),
        "3位(%)": ((rank_df[rank_df == 3].count()) / rank_df.count() * 100).round(2),
        "4位(%)": ((rank_df[rank_df == 4].count()) / rank_df.count() * 100).round(2),
        "平均順位": rank_df.mean().round(2),
        "区間ポイント": point_sum_df.sum().round(1),
        "区間平均": point_sum_df.mean().round(1),
        "通算ポイント": point_df.round(1),
    }
    count_df = pd.DataFrame(count_stats)

    count_df.loc[total_index] = {
        "ゲーム数": count_df["ゲーム数"].sum().astype("int"),
        "1位": count_df["1位"].sum().astype("int"),
        "2位": count_df["2位"].sum().astype("int"),
        "3位": count_df["3位"].sum().astype("int"),
        "4位": count_df["4位"].sum().astype("int"),
        "1位(%)": (count_df["1位"].sum() / count_df["ゲーム数"].sum() * 100).round(2),
        "2位(%)": (count_df["2位"].sum() / count_df["ゲーム数"].sum() * 100).round(2),
        "3位(%)": (count_df["3位"].sum() / count_df["ゲーム数"].sum() * 100).round(2),
        "4位(%)": (count_df["4位"].sum() / count_df["ゲーム数"].sum() * 100).round(2),
        "平均順位": player_df["rank"].mean().round(2),
        "区間ポイント": player_df["point"].sum().round(1),
        "区間平均": player_df["point"].mean().round(1),
    }
    #
    rank_table = pd.DataFrame()
    rank_table["ゲーム数"] = count_df["ゲーム数"]
    rank_table["1位"] = count_df.apply(lambda row: "{:.2f}% ({:.0f})".format(row["1位(%)"], row["1位"]), axis=1)
    rank_table["2位"] = count_df.apply(lambda row: "{:.2f}% ({:.0f})".format(row["2位(%)"], row["2位"]), axis=1)
    rank_table["3位"] = count_df.apply(lambda row: "{:.2f}% ({:.0f})".format(row["3位(%)"], row["3位"]), axis=1)
    rank_table["4位"] = count_df.apply(lambda row: "{:.2f}% ({:.0f})".format(row["4位(%)"], row["4位"]), axis=1)
    rank_table["平均順位"] = count_df.apply(lambda row: "{:.2f}".format(row["平均順位"]), axis=1)

    # グラフ設定
    f.common.graph_setup(plt, fm)
    fig = plt.figure(figsize=(20, 10))
    fig.suptitle(title_text, size=20, weight="bold")
    gs = gridspec.GridSpec(figure=fig, nrows=3, ncols=2)

    ax_rpoint1 = fig.add_subplot(gs[2, 0])
    ax_rpoint2 = fig.add_subplot(gs[2, 1])
    ax_point1 = fig.add_subplot(gs[0, 0])
    ax_point2 = fig.add_subplot(gs[0, 1])
    ax_rank1 = fig.add_subplot(gs[1, 0])
    ax_rank2 = fig.add_subplot(gs[1, 1])

    plt.subplots_adjust(wspace=0.22, hspace=0.18)

    # 素点データ
    subplot_box(rpoint_df, ax_rpoint1)
    subplot_table(stats_df, ax_rpoint2)

    # ポイントデータ
    point_df.plot(  # レイアウト調整用ダミー
        ax=ax_point1,
        kind="bar",
        alpha=0,
    )
    point_df.plot(
        ax=ax_point1,
        kind="line",
        title="ポイント推移",
        ylabel="通算ポイント(pt)",
        y=point_df.values.tolist(),
        x=point_df.index.to_list(),
        marker="o",
        color="b",
    )
    # Y軸修正
    ylabs = ax_point1.get_yticks()[1:-1]
    ax_point1.set_yticks(ylabs)
    ax_point1.set_yticklabels(
        [str(int(ylab)).replace("-", "▲") for ylab in ylabs]
    )

    xxx2 = count_df.apply(lambda col: col.map(lambda x: x if isinstance(x, int) else f"{x:+.1f}"))
    subplot_table(xxx2.filter(items=["ゲーム数", "区間ポイント", "区間平均", "通算ポイント"]), ax_point2)

    # 順位データ
    ax_rank_avg = ax_rank1.twinx()
    count_df.filter(items=["平均順位"]).drop(index=total_index).plot(
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
    ax_rank_avg.yaxis
    ax_rank_avg.invert_yaxis()
    ax_rank_avg.axhline(y=2.5, linewidth=0.5, ls="dashed", color="grey")

    filter_items = ["1位(%)", "2位(%)", "3位(%)", "4位(%)"]
    count_df.filter(items=filter_items).drop(index=total_index).plot(
        ax=ax_rank1,
        kind="bar",
        title="獲得順位",
        ylabel="獲得順位(%)",
        colormap="Set2",
        stacked=True,
        rot=90,
        ylim=[-5, 105],
    )
    h1, l1 = ax_rank1.get_legend_handles_labels()
    h2, l2 = ax_rank_avg.get_legend_handles_labels()
    ax_rank1.legend(
        h1 + h2,
        l1 + l2,
        bbox_to_anchor=(0.5, 0),
        loc="lower center",
        ncol=5,
    )

    subplot_table(rank_table, ax_rank2)

    plt.savefig(save_file, bbox_inches="tight")
    plt.close()
    return (len(player_df), save_file)


def get_data(df, interval):
    # interval単位で分割
    rpoint_data = {}

    s = 0
    e = len(df) % interval
    if e:
        rpoint_data[f"{(s + 1):3d}G - {e:3d}G"] = ([None] * interval + df[s:e].to_list())[-interval::]

    for x in range(int(len(df) / interval)):
        s = len(df) % interval + interval * x
        e = s + interval
        rpoint_data[f"{(s + 1):3d}G - {e:3d}G"] = df[s:e].to_list()

    return (pd.DataFrame(rpoint_data))


def subplot_box(df, ax):

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


def subplot_table(df, ax):
    df = df.apply(lambda col: col.map(lambda x: str(x).replace("-", "▲")))
    df.replace("+nan", "-----", inplace=True)
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        rowLabels=df.index,
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    ax.axis("off")
