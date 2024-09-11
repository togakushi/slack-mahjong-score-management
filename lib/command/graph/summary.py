import logging
import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

import global_value as g
from lib import database as d
from lib import function as f

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)


def point_plot():
    """
    ポイント推移グラフを生成する

    Returns
    -------
    total_game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    plt.close()
    # データ収集
    game_info = d.aggregate.game_info()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        return (len(target_data), f.message.no_hits())

    # グラフタイトル/X軸ラベル
    pivot_index = "playtime"
    if g.prm.target_count:
        title_text = f"ポイント推移 (直近 {g.prm.target_count} ゲーム)"
        xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
    else:
        match g.opt.collection:
            case "daily":
                xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
                if g.prm.starttime_ymd == g.prm.endonday_ymd:
                    title_text = f"通算ポイント ({g.prm.starttime_ymd})"
                else:
                    title_text = f"ポイント推移 ({g.prm.starttime_ymd} - {g.prm.endonday_ymd})"
            case "monthly":
                xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
                if g.prm.starttime_ym == g.prm.endonday_ym:
                    title_text = f"通算ポイント ({g.prm.starttime_ym})"
                else:
                    title_text = f"ポイント推移 ({g.prm.starttime_ym} - {g.prm.endonday_ym})"
            case _:
                if g.opt.search_word:
                    pivot_index = "comment"
                    xlabel_text = f"（総ゲーム数：{game_info['game_count']} ）"
                    if game_info["first_comment"] == game_info["last_comment"]:
                        title_text = "通算ポイント ({})".format(
                            game_info["first_comment"],
                        )
                    else:
                        title_text = "ポイント推移 ({} - {})".format(
                            game_info["first_comment"],
                            game_info["last_comment"]
                        )
                else:
                    xlabel_text = f"ゲーム終了日時（{game_info['game_count']} ゲーム）"
                    title_text = f"ポイント推移 ({g.prm.starttime_hm} - {g.prm.endtime_hm})"
                    if g.prm.starttime_ymd == g.prm.endonday_ymd and game_info["game_count"] == 1:
                        title_text = f"通算ポイント ({g.prm.starttime_ymd})"

    # 集計
    if g.opt.team_total:
        legend = "チーム名"
        pivot = pd.pivot_table(
            df, index=pivot_index, columns="team", values="point_sum"
        ).ffill()
    else:
        legend = "プレイヤー名"
        pivot = pd.pivot_table(
            df, index=pivot_index, columns="プレイヤー名", values="point_sum"
        ).ffill()

    pivot = pivot.reindex(  # 並び替え
        target_data[legend].to_list(), axis="columns"
    )

    # グラフ生成
    args = {
        "kind": "point",
        "title_text": title_text,
        "total_game_count": game_info["game_count"],
        "target_data": target_data,
        "legend": legend,
        "xlabel_text": xlabel_text,
        "ylabel_text": "通算ポイント",
        "horizontal": True,
    }
    save_file = _graph_generation(pivot, **args)
    plt.savefig(save_file, bbox_inches="tight")

    return (game_info["game_count"], save_file)


def rank_plot():
    """
    順位変動グラフを生成する

    Returns
    -------
    total_game_count : int
        グラフにプロットしたゲーム数

    text : text
        検索結果が0件のときのメッセージ or
        グラフ画像保存パス
    """

    # データ収集
    game_info = d.aggregate.game_info()
    target_data, df = _data_collection()

    if target_data.empty:  # 描写対象が0人の場合は終了
        return (len(target_data), f.message.no_hits())

    # グラフタイトル/X軸ラベル
    pivot_index = "playtime"
    if g.prm.target_count:
        title_text = f"順位推移 (直近 {g.prm.target_count} ゲーム)"
        xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
    else:
        match g.opt.collection:
            case "daily":
                xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
                if g.prm.starttime_ymd == g.prm.endonday_ymd:
                    title_text = f"順位 ({g.prm.starttime_ymd})"
                else:
                    title_text = f"順位推移 ({g.prm.starttime_ymd} - {g.prm.endonday_ymd})"
            case "monthly":
                xlabel_text = f"集計日（総ゲーム数：{game_info['game_count']}）"
                if g.prm.starttime_ym == g.prm.endonday_ym:
                    title_text = f"順位 ({g.prm.starttime_ym})"
                else:
                    title_text = f"順位推移 ({g.prm.starttime_ym} - {g.prm.endonday_ym})"
            case _:
                if g.opt.search_word:
                    pivot_index = "comment"
                    xlabel_text = f"（総ゲーム数：{game_info['game_count']} ）"
                    if game_info["first_comment"] == game_info["last_comment"]:
                        title_text = "順位 ({})".format(
                            game_info["first_comment"],
                        )
                    else:
                        title_text = "順位推移 ({} - {})".format(
                            game_info["first_comment"],
                            game_info["last_comment"]
                        )
                else:
                    xlabel_text = f"ゲーム終了日時（{game_info['game_count']} ゲーム）"
                    title_text = f"順位推移 ({g.prm.starttime_hm} - {g.prm.endtime_hm})"
                    if g.prm.starttime_ymd == g.prm.endonday_ymd and game_info["game_count"] == 1:
                        title_text = f"順位 ({g.prm.starttime_ymd})"

    # 集計
    if g.opt.team_total:
        legend = "チーム名"
        pivot = pd.pivot_table(
            df, index=pivot_index, columns="team", values="point_sum"
        ).ffill()
    else:
        legend = "プレイヤー名"
        pivot = pd.pivot_table(
            df, index=pivot_index, columns=legend, values="point_sum"
        ).ffill()

    pivot = pivot.reindex(  # 並び替え
        target_data[legend].to_list(), axis="columns"
    )
    pivot = pivot.rank(method="dense", ascending=False, axis=1)

    # グラフ生成
    args = {
        "kind": "rank",
        "title_text": title_text,
        "total_game_count": game_info["game_count"],
        "target_data": target_data,
        "legend": legend,
        "xlabel_text": xlabel_text,
        "ylabel_text": "順位 (通算ポイント順)",
        "horizontal": False,
    }
    save_file = _graph_generation(pivot, **args)
    plt.savefig(save_file, bbox_inches="tight")

    return (game_info["game_count"], save_file)


def _data_collection():
    """
    データ収集
    """

    # データ収集
    g.opt.fourfold = True  # 直近Nは4倍する(縦持ちなので4人分)

    target_data = pd.DataFrame()
    if g.opt.team_total:  # チーム戦
        df = d.aggregate.team_gamedata()
        if df.empty:
            return (target_data, df)

        target_data["last_point"] = df.groupby("team").last()["point_sum"]
        target_data["game_count"] = (
            df.groupby("team").max(numeric_only=True)["count"]
        )
        target_data["チーム名"] = target_data.index
        target_data = target_data.sort_values("last_point", ascending=False)
    else:  # 個人戦
        df = d.aggregate.personal_gamedata()
        if df.empty:
            return (target_data, df)

        target_data["プレイヤー名"] = df.groupby("name").last()["プレイヤー名"]
        target_data["last_point"] = df.groupby("name").last()["point_sum"]
        target_data["game_count"] = (
            df.groupby("name").max(numeric_only=True)["count"]
        )

        # 足切り
        target_list = list(
            target_data.query("game_count >= @g.opt.stipulated").index
        )
        _ = target_list  # ignore PEP8 F841
        target_data = target_data.query("name == @target_list").copy()
        df = df.query("name == @target_list").copy()

    # 順位付け
    target_data["position"] = (
        target_data["last_point"].rank(ascending=False).astype(int)
    )

    return (target_data.sort_values("position"), df)


def _graph_generation(df: pd.DataFrame, **kwargs):
    """
    グラフ生成共通処理
    """

    save_file = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "graph.png"
    )

    f.common.graph_setup(plt, fm)
    if all(df.count() == 1) and kwargs["horizontal"]:
        kwargs["kind"] = "barh"
        lab = []
        color = []
        for _, v in kwargs["target_data"].iterrows():
            lab.append("{:2d}位 ： {} ({}pt / {}G)".format(
                v["position"],
                v[kwargs["legend"]],
                "{:+.1f}".format(v["last_point"]).replace("-", "▲"),
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

        tmpdf.plot.barh(
            figsize=(8, 2 + tmpdf.count().iloc[0] / 5),
            y="point",
            color=color[::-1],
        )

        plt.legend().remove()
        plt.gca().yaxis.tick_right()
        plt.gca().set_axisbelow(True)

        # X軸修正
        xlocs, xlabs = plt.xticks()
        new_xlabs = [xlab.get_text().replace("−", "▲") for xlab in xlabs]
        plt.xticks(xlocs[1:-1], new_xlabs[1:-1])

        logging.info(f"plot data:\n{tmpdf}")
    else:
        df.plot(
            figsize=(8, 6),
            xlabel=kwargs["xlabel_text"],
            ylabel=kwargs["ylabel_text"],
            marker="." if len(df) < 50 else None,
        )

        # 凡例
        legend_text = []
        for _, v in kwargs["target_data"].iterrows():
            legend_text.append("{}位 ： {} ({}pt / {}G)".format(
                v["position"], v[kwargs["legend"]],
                "{:+.1f}".format(v["last_point"]).replace("-", "▲"),
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
        plt.yticks(ylocs[1:-1], new_ylabs[1:-1])

        logging.info(f"plot data:\n{df}")

    #
    match kwargs["kind"]:
        case "point":
            plt.axhline(y=0, linewidth=0.5, ls="dashed", color="grey")
        case "rank":
            plt.yticks(
                list(range(len(kwargs["target_data"]) + 1))[1::2],
                list(range(len(kwargs["target_data"]) + 1))[1::2]
            )
            plt.gca().invert_yaxis()

    plt.title(
        kwargs["title_text"],
        fontsize=16,
    )

    return (save_file)
