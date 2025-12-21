"""
libs/commands/report/results_list.py
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

import libs.global_value as g
from libs.data import loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.types import StyleOptions
from libs.utils import formatter, graphutil, textutil

if TYPE_CHECKING:
    import pandas as pd

    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType


def main(m: "MessageParserProtocol"):
    """成績一覧表を生成する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 検索動作を合わせる
    g.params.update({"guest_skip": g.params["guest_skip2"]})

    # --- データ取得
    game_info = GameInfo()
    df = loader.read_data("REPORT_RESULTS_LIST").reset_index(drop=True)
    df.index = df.index + 1
    if df.empty:
        m.post.headline = {"成績一覧": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    # 見出し設定
    if g.params.get("individual"):
        title = "個人成績一覧"
        df = df.rename(columns={"name": "player"})
    else:  # チーム集計
        title = "チーム成績一覧"
        df = df.rename(columns={"name": "team"})

    # 非表示項目
    if g.cfg.mahjong.ignore_flying or g.cfg.dropitems.report & g.cfg.dropitems.flying:
        df = df.drop(columns=["flying_mix", "flying_count", "flying_rate"])
    if g.cfg.dropitems.report & g.cfg.dropitems.yakuman:
        df = df.drop(columns=["yakuman_mix", "yakuman_count", "yakuman_rate"])

    file_path: "MessageType"
    match str(g.params.get("format", "default")).lower():
        case "text" | "txt":
            file_path = text_generation(df)
        case "csv":
            file_path = csv_generation(df)
        case _:
            file_path = graph_generation(game_info, df, title)

    m.post.headline = {title: message.header(game_info, m)}
    match g.adapter.interface_type:
        case "slack":
            m.set_data(title, file_path, StyleOptions(use_comment=True, header_hidden=True))
        case "web":
            m.set_data("", df_generation(df), StyleOptions())


def graph_generation(game_info: GameInfo, df: "pd.DataFrame", title: str) -> "MessageType":
    """グラフ生成処理

    Args:
        game_info (GameInfo): ゲーム情報
        df (pd.DataFrame): 描写データ
        title (str): グラフタイトル

    Returns:
        MessageType: 生成ファイルパス
    """

    if g.adapter.conf.plotting_backend == "plotly":
        return None

    df = formatter.df_rename(
        df.filter(
            items=[
                "player",
                "team",
                "game",
                "total_mix",
                "avg_mix",
                "rank_avg",
                "1st_mix",
                "2nd_mix",
                "3rd_mix",
                "4th_mix",
                "rank_dist",
                "flying_mix",
                "yakuman_mix",
            ]
        )
    )

    # フォント/色彩設定
    graphutil.setup()
    report_file_path = textutil.save_file_path("report.png")
    plt.rcParams["font.size"] = 6

    match (plt.rcParams["text.color"], plt.rcParams["figure.facecolor"]):
        case text_color, bg_color if text_color == "black" and bg_color == "white":
            line_color1 = "#dddddd"
            line_color2 = "#ffffff"
        case text_color, bg_color if text_color == "white" and bg_color == "black":
            line_color1 = "#111111"
            line_color2 = "#000000"
        case _:
            line_color1 = plt.rcParams["figure.facecolor"]
            line_color2 = plt.rcParams["figure.facecolor"]

    column_color = ["#000080"] * len(df.columns)
    cell_color = []
    for x in range(len(df)):
        if int(x % 2):
            cell_color.append([line_color1] * len(df.columns))
        else:
            cell_color.append([line_color2] * len(df.columns))

    fig = plt.figure(figsize=(8, (len(df) * 0.2) + 0.8), dpi=200, tight_layout=True)
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title(title, fontsize=12)
    tb = plt.table(
        cellText=df.values,
        colLabels=df.columns,
        colColours=column_color,
        cellColours=cell_color,
        loc="center",
    )

    tb.auto_set_font_size(False)
    tb.auto_set_column_width(range(len(df)))
    for i in range(len(df.columns)):
        tb[0, i].set_text_props(color="#FFFFFF", weight="bold")
        for j in range(len(df) + 1):
            tb[j, i].set_text_props(ha="center")

    # 追加テキスト
    remark_text = "".join(compose.text_item.remarks(True)) + compose.text_item.search_word(True)
    add_text = "[検索範囲：{}] [総ゲーム数：{}] {}".format(
        compose.text_item.search_range(time_pattern="time"),
        game_info.count,
        f"[{remark_text}]" if remark_text else "",
    )

    fig.text(
        0.01,
        0.01,  # 表示位置(左下0,0 右下0,1)
        add_text,
        transform=fig.transFigure,
        fontsize=6,
    )

    fig.savefig(report_file_path)
    return report_file_path


def text_generation(df: "pd.DataFrame") -> "MessageType":
    """テキストテーブル生成

    Args:
        df (pd.DataFrame): 描写データ

    Returns:
        MessageType: 生成ファイルパス
    """

    report_file_path = g.cfg.setting.work_dir / (f"{g.params['filename']}.txt" if g.params.get("filename") else "report.txt")

    df = df.filter(
        items=[
            "player",
            "team",
            "game",
            "point_sum",
            "point_avg",
            "1st_count",
            "rank1_rate",
            "2nd_count",
            "rank2_rate",
            "3rd_count",
            "rank3_rate",
            "4th_count",
            "rank4_rate",
            "rank_avg",
            "flying_count",
            "flying_rate",
            "yakuman_count",
            "yakuman_rate",
        ]
    )
    fmt = formatter.floatfmt_adjust(df, index=True)
    df = formatter.df_rename(df)
    df.to_markdown(report_file_path, tablefmt="outline", floatfmt=fmt)

    return report_file_path


def csv_generation(df: "pd.DataFrame") -> "MessageType":
    """CSV生成

    Args:
        df (pd.DataFrame): 描写データ

    Returns:
        MessageType: 生成ファイルパス
    """

    report_file_path = g.cfg.setting.work_dir / (f"{g.params['filename']}.csv" if g.params.get("filename") else "report.csv")

    df = df.filter(
        items=[
            "player",
            "team",
            "game",
            "point_sum",
            "point_avg",
            "1st_count",
            "rank1_rate",
            "2nd_count",
            "rank2_rate",
            "3rd_count",
            "rank3_rate",
            "4th_count",
            "rank4_rate",
            "rank_avg",
            "flying_count",
            "flying_rate",
            "yakuman_count",
            "yakuman_rate",
        ]
    )

    for x in df.columns:
        match x:
            case "point_sum" | "point_avg":
                df[x] = df[x].round(1)
            case "rank1_rate" | "rank2_rate" | "rank3_rate" | "rank4_rate" | "flying_rate" | "yakuman_rate":
                df[x] = df[x].round(2)
            case "rank_avg":
                df[x] = df[x].astype(float).round(2)

    df.to_csv(report_file_path)

    return report_file_path


def df_generation(df: "pd.DataFrame") -> "MessageType":
    """テキストテーブル生成

    Args:
        df (pd.DataFrame): 描写データ

    Returns:
        MessageType: 整形データ
    """

    df = df.filter(
        items=[
            "player",
            "team",
            "game",
            "point_sum",
            "point_avg",
            "1st_count",
            "rank1_rate",
            "2nd_count",
            "rank2_rate",
            "3rd_count",
            "rank3_rate",
            "4th_count",
            "rank4_rate",
            "rank_avg",
            "flying_count",
            "flying_rate",
            "yakuman_count",
            "yakuman_rate",
        ]
    )

    return formatter.df_rename(df)
