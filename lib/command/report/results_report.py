import logging
import os
import sqlite3
from datetime import datetime
from io import BytesIO
from typing import List, Tuple

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, LongTable, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, TableStyle)

import lib.global_value as g
from lib import command as c
from lib.database.common import load_query, query_modification

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)

pd.set_option("display.max_rows", None)


def get_game_results() -> list:
    """月/年単位のゲーム結果集計

    Returns:
        list: 集計結果のリスト
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(
        query_modification(load_query("lib/queries/report/personal_data.sql")),
        g.prm.to_dict(),
    )

    # --- データ収集
    results = [
        [
            "",
            "ゲーム数",
            "通算\nポイント",
            "平均\nポイント",
            "1位", "",
            "2位", "",
            "3位", "",
            "4位", "",
            "平均\n順位",
            "トビ", "",
        ]
    ]

    for row in rows.fetchall():
        if row["ゲーム数"] == 0:
            break

        results.append(
            [
                row["集計"],
                row["ゲーム数"],
                str(row["通算ポイント"]).replace("-", "▲") + "pt",
                str(row["平均ポイント"]).replace("-", "▲") + "pt",
                row["1位"], f"{row['1位率']:.2f}%",
                row["2位"], f"{row['2位率']:.2f}%",
                row["3位"], f"{row['3位率']:.2f}%",
                row["4位"], f"{row['4位率']:.2f}%",
                f"{row['平均順位']:.2f}",
                row["トビ"], f"{row['トビ率']:.2f}%",
            ]
        )
    logging.info("return record: %s", len(results))
    resultdb.close()

    if len(results) == 1:  # ヘッダのみ
        return ([])

    return (results)


def get_count_results(game_count: int) -> list:
    """指定間隔区切りのゲーム結果集計

    Args:
        game_count (int): 区切るゲーム数

    Returns:
        list: 集計結果のリスト
    """

    g.prm.append({"interval": game_count})

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(
        query_modification(load_query("lib/queries/report/count_data.sql")),
        g.prm.to_dict(),
    )

    # --- データ収集
    results = [
        [
            "開始",
            "終了",
            "ゲーム数",
            "通算\nポイント",
            "平均\nポイント",
            "1位", "",
            "2位", "",
            "3位", "",
            "4位", "",
            "平均\n順位",
            "トビ", "",
        ]
    ]

    for row in rows.fetchall():
        if row["ゲーム数"] == 0:
            break

        results.append(
            [
                row["開始"],
                row["終了"],
                row["ゲーム数"],
                str(row["通算ポイント"]).replace("-", "▲") + "pt",
                str(row["平均ポイント"]).replace("-", "▲") + "pt",
                row["1位"], f"{row['1位率']:.2f}%",
                row["2位"], f"{row['2位率']:.2f}%",
                row["3位"], f"{row['3位率']:.2f}%",
                row["4位"], f"{row['4位率']:.2f}%",
                f"{row['平均順位']:.2f}",
                row["トビ"], f"{row['トビ率']:.2f}%",
            ]
        )
    logging.info("return record: %s", len(results))
    resultdb.close()

    if len(results) == 1:  # ヘッダのみ
        return ([])

    return (results)


def get_count_moving(game_count: int) -> list:
    """移動平均を取得する

    Args:
        game_count (int): 平滑化するゲーム数

    Returns:
        list: 集計結果のリスト
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row

    g.prm.append({"interval": game_count})
    rows = resultdb.execute(
        query_modification(load_query("lib/queries/report/count_moving.sql")),
        g.prm.to_dict(),
    )

    # --- データ収集
    results = []
    for row in rows.fetchall():
        results.append(dict(row))

    logging.info("return record: %s", len(results))
    resultdb.close()

    return (results)


def graphing_mean_rank(df: pd.DataFrame, title: str, whole: bool = False) -> BytesIO:
    """平均順位の折れ線グラフを生成

    Args:
        df (pd.DataFrame): 描写データ
        title (str): グラフタイトル
        whole (bool, optional): 集計種別. Defaults to False.
            - True: 全体集計
            - False: 指定範囲集計

    Returns:
        BytesIO: 画像データ
    """

    imgdata = BytesIO()

    if whole:
        df.plot(
            kind="line",
            figsize=(12, 5),
            fontsize=14,
        )
        plt.legend(
            title="開始 - 終了",
            ncol=int(len(df.columns) / 5) + 1,
        )
    else:
        df.plot(
            kind="line",
            y="rank_avg",
            x="game_no",
            legend=False,
            figsize=(12, 5),
            fontsize=14,
        )

    plt.title(title, fontsize=18)
    plt.grid(axis="y")

    # Y軸設定
    plt.ylabel("平均順位", fontsize=14)
    plt.yticks([4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0])
    for ax in plt.gcf().get_axes():  # 逆向きにする
        ax.invert_yaxis()

    # X軸設定
    plt.xlabel("ゲーム数", fontsize=14)

    plt.savefig(imgdata, format="jpg", bbox_inches="tight")
    plt.close()

    return (imgdata)


def graphing_total_points(df: pd.DataFrame, title: str, whole: bool = False) -> BytesIO:
    """通算ポイント推移の折れ線グラフを生成

    Args:
        df (pd.DataFrame): 描写データ
        title (str): グラフタイトル
        whole (bool, optional): 集計種別. Defaults to False.
            - True: 全体集計 / 移動平均付き
            - False: 指定範囲集計
    Returns:
        BytesIO: 画像データ
    """

    imgdata = BytesIO()

    if whole:
        df.plot(
            kind="line",
            figsize=(12, 8),
            fontsize=14,
        )
        plt.legend(
            title="通算 （ 開始 - 終了 ）",
            ncol=int(len(df.columns) / 5) + 1,
        )
    else:
        point_sum = df.plot(
            kind="line",
            y="point_sum",
            label="通算",
            figsize=(12, 8),
            fontsize=14,
        )
        if len(df) > 50:
            point_sum = df["point_sum"].rolling(40).mean().plot(
                kind="line", label="移動平均(40ゲーム)",
                ax=point_sum,
            )
        if len(df) > 100:
            point_sum = df["point_sum"].rolling(80).mean().plot(
                kind="line", label="移動平均(80ゲーム)",
                ax=point_sum,
            )
        plt.legend()

    plt.title(title, fontsize=18)
    plt.grid(axis="y")

    # Y軸設定
    plt.ylabel("ポイント", fontsize=14)
    ylocs, ylabs = plt.yticks()
    new_ylabs = [ylab.get_text().replace("−", "▲") for ylab in ylabs]
    plt.yticks(list(ylocs[1:-1]), new_ylabs[1:-1])

    # X軸設定
    plt.xlabel("ゲーム数", fontsize=14)

    plt.savefig(imgdata, format="jpg", bbox_inches="tight")
    plt.close()

    return (imgdata)


def graphing_rank_distribution(df: pd.DataFrame, title: str) -> BytesIO:
    """順位分布の棒グラフを生成

    Args:
        df (pd.DataFrame): 描写データ
        title (str): グラフタイトル

    Returns:
        BytesIO: 画像データ
    """

    imgdata = BytesIO()

    df.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 7),
        fontsize=14,
    )

    plt.title(title, fontsize=18)
    plt.legend(
        bbox_to_anchor=(0.5, 0),
        loc="lower center",
        ncol=4,
        fontsize=12,
    )

    # Y軸設定
    plt.yticks([0, 25, 50, 75, 100])
    plt.ylabel("（％）", fontsize=14)
    for ax in plt.gcf().get_axes():  # グリッド線を背後にまわす
        ax.set_axisbelow(True)
        plt.grid(axis="y")

    # X軸設定
    if len(df) > 10:
        plt.xticks(rotation=30, ha="right")
    else:
        plt.xticks(rotation=30)

    plt.savefig(imgdata, format="jpg", bbox_inches="tight")
    plt.close()

    return (imgdata)


def gen_pdf() -> Tuple[str | bool, str | bool]:
    """成績レポートを生成する

    Returns:
        Tuple[str | bool, str | bool]:
            - str: レポート対象メンバー名
            - str: レポート保存パス
    """

    plt.close()

    if not g.prm.player_name:  # レポート対象の指定なし
        return (False, False)

    # 対象メンバーの記録状況
    target_info = c.member.member_info(g.prm.player_name)
    logging.info(target_info)

    if not target_info["game_count"] > 0:  # 記録なし
        return (False, False)

    # 書式設定
    font_path = os.path.join(os.path.realpath(os.path.curdir), g.cfg.setting.font_file)
    pdf_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.pdf" if g.opt.filename else "Results.pdf"
    )
    pdfmetrics.registerFont(TTFont("ReportFont", font_path))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        topMargin=10.0 * mm,
        bottomMargin=10.0 * mm,
        # leftMargin=1.5 * mm,
        # rightMargin=1.5 * mm,
    )

    style: dict = {}
    style["Title"] = ParagraphStyle(
        name="Title", fontName="ReportFont", fontSize=24
    )
    style["Normal"] = ParagraphStyle(
        name="Normal", fontName="ReportFont", fontSize=14
    )
    style["Left"] = ParagraphStyle(
        name="Left", fontName="ReportFont", fontSize=14, alignment=TA_LEFT
    )
    style["Right"] = ParagraphStyle(
        name="Right", fontName="ReportFont", fontSize=14, alignment=TA_RIGHT
    )

    plt.rcParams.update(plt.rcParamsDefault)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()
    fm.fontManager.addfont(font_path)

    # レポート作成
    elements: list = []
    elements.extend(cover_page(style, target_info))  # 表紙
    elements.extend(entire_aggregate(style))  # 全期間
    elements.extend(periodic_aggregation(style))  # 期間集計
    elements.extend(sectional_aggregate(style, target_info))  # 区間集計

    doc.build(elements)
    logging.notice("report generation: %s", g.prm.player_name)  # type: ignore

    return (g.prm.player_name, pdf_path)


def cover_page(style: dict, target_info: dict) -> list:
    """表紙生成

    Args:
        style (dict): レイアウトスタイル
        target_info (dict): プレイヤー情報

    Returns:
        list: 生成内容
    """

    elements: list = []

    first_game = datetime.fromtimestamp(  # 最初のゲーム日時
        float(target_info["first_game"])
    )
    last_game = datetime.fromtimestamp(  # 最後のゲーム日時
        float(target_info["last_game"])
    )

    if g.opt.anonymous:
        target_player = c.member.name_replace(g.prm.player_name)
    else:
        target_player = g.prm.player_name

    # 表紙
    elements.append(Spacer(1, 40 * mm))
    elements.append(Paragraph(f"成績レポート：{target_player}", style["Title"]))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        "集計期間：{} - {}".format(  # pylint: disable=consider-using-f-string
            first_game.strftime("%Y-%m-%d %H:%M"),
            last_game.strftime("%Y-%m-%d %H:%M"),
        ), style["Normal"]
    ))
    elements.append(Spacer(1, 100 * mm))
    elements.append(
        Paragraph(
            f"作成日：{datetime.now().strftime('%Y-%m-%d')}",
            style["Right"]
        )
    )
    elements.append(PageBreak())

    return (elements)


def entire_aggregate(style: dict) -> list:
    """全期間

    Args:
        style (dict): レイアウトスタイル

    Returns:
        list: 生成内容
    """

    elements: list = []

    elements.append(Paragraph("全期間", style["Left"]))
    elements.append(Spacer(1, 5 * mm))
    data: list = []
    g.prm.aggregate_unit = "A"
    tmp_data = get_game_results()

    if not tmp_data:
        return ([])

    for _, val in enumerate(tmp_data):  # ゲーム数を除外
        data.append(val[1:])
    tt = LongTable(data, repeatRows=1)
    tt.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ('SPAN', (3, 0), (4, 0)),
        ('SPAN', (5, 0), (6, 0)),
        ('SPAN', (7, 0), (8, 0)),
        ('SPAN', (9, 0), (10, 0)),
        ('SPAN', (12, 0), (13, 0)),
        # ヘッダ行
        ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))
    elements.append(tt)

    # 順位分布
    imgdata = BytesIO()
    gdata = pd.DataFrame(
        {
            "順位分布": [
                float(data[1][4].replace("%", "")),
                float(data[1][6].replace("%", "")),
                float(data[1][8].replace("%", "")),
                float(data[1][10].replace("%", "")),
            ],
        }, index=["1位率", "2位率", "3位率", "4位率"]
    )
    gdata.plot(
        kind="pie",
        y="順位分布",
        labels=None,
        figsize=(6, 6),
        fontsize=14,
        autopct="%.2f%%",
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    plt.title("順位分布 （ 全期間 ）", fontsize=18)
    plt.ylabel("")
    plt.legend(
        list(gdata.index),
        bbox_to_anchor=(0.5, -0.1),
        loc="lower center",
        ncol=4,
        fontsize=12
    )
    plt.savefig(imgdata, format="jpg", bbox_inches="tight")

    elements.append(Spacer(1, 5 * mm))
    elements.append(Image(imgdata, width=600 * 0.5, height=600 * 0.5))
    plt.close()

    data = get_count_moving(0)
    df = pd.DataFrame(data)
    df["playtime"] = pd.to_datetime(df["playtime"])

    # 通算ポイント推移
    imgdata = graphing_total_points(df, "通算ポイント推移 （ 全期間 ）", False)
    elements.append(Image(imgdata, width=1200 * 0.5, height=800 * 0.5))

    # 平均順位
    imgdata = graphing_mean_rank(df, "平均順位推移 （ 全期間 ）", False)
    elements.append(Image(imgdata, width=1200 * 0.5, height=500 * 0.5))

    elements.append(PageBreak())

    return (elements)


def periodic_aggregation(style: dict) -> list:
    """期間集計

    Args:
        style (dict): レイアウトスタイル

    Returns:
        list: 生成内容
    """

    elements: list = []

    pattern: List[Tuple[str, str, str]] = [
        # 表タイトル, グラフタイトル, フラグ
        ("月別集計", "順位分布（月別）", "M"),
        ("年別集計", "順位分布（年別）", "Y"),
    ]

    for table_title, graph_title, flag in pattern:
        elements.append(Paragraph(table_title, style["Left"]))
        elements.append(Spacer(1, 5 * mm))

        data: list = []
        g.prm.aggregate_unit = flag
        tmp_data = get_game_results()

        if not tmp_data:
            return ([])

        for _, val in enumerate(tmp_data):  # 日時を除外
            data.append(val[:15])

        tt = LongTable(data, repeatRows=1)
        ts = TableStyle([
            ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ('SPAN', (4, 0), (5, 0)),
            ('SPAN', (6, 0), (7, 0)),
            ('SPAN', (8, 0), (9, 0)),
            ('SPAN', (10, 0), (11, 0)),
            ('SPAN', (13, 0), (14, 0)),
            # ヘッダ行
            ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])

        if len(data) > 4:
            for i in range(len(data) - 2):
                if i % 2 == 0:
                    ts.add("BACKGROUND", (0, i + 2), (-1, i + 2), colors.lightgrey)
        tt.setStyle(ts)
        elements.append(tt)
        elements.append(Spacer(1, 10 * mm))

        # 順位分布
        df = pd.DataFrame(
            {
                "1位率": [float(data[x + 1][5].replace("%", "")) for x in range(len(data) - 1)],
                "2位率": [float(data[x + 1][7].replace("%", "")) for x in range(len(data) - 1)],
                "3位率": [float(data[x + 1][9].replace("%", "")) for x in range(len(data) - 1)],
                "4位率": [float(data[x + 1][11].replace("%", "")) for x in range(len(data) - 1)],
            }, index=[data[x + 1][0] for x in range(len(data) - 1)]
        )

        imgdata = graphing_rank_distribution(df, graph_title)
        elements.append(Spacer(1, 5 * mm))
        elements.append(Image(imgdata, width=1200 * 0.5, height=700 * 0.5))

        elements.append(PageBreak())

    return (elements)


def sectional_aggregate(style: dict, target_info: dict) -> list:
    """区間集計

    Args:
        style (dict): レイアウトスタイル
        target_info (dict): プレイヤー情報

    Returns:
        list: 生成内容
    """

    elements: list = []

    pattern: List[Tuple[int, int, str]] = [
        # 区切り回数, 閾値, タイトル
        (80, 100, "短期"),
        (200, 240, "中期"),
        (400, 500, "長期"),
    ]

    for count, threshold, title in pattern:
        if target_info["game_count"] > threshold:
            # テーブル
            elements.append(Paragraph(f"区間集計 （ {title} ）", style["Left"]))
            elements.append(Spacer(1, 5 * mm))
            data = get_count_results(count)

            if not data:
                return ([])

            tt = LongTable(data, repeatRows=1)
            ts = TableStyle([
                ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ('SPAN', (5, 0), (6, 0)),
                ('SPAN', (7, 0), (8, 0)),
                ('SPAN', (9, 0), (10, 0)),
                ('SPAN', (11, 0), (12, 0)),
                ('SPAN', (14, 0), (15, 0)),
                # ヘッダ行
                ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ])
            if len(data) > 4:
                for i in range(len(data) - 2):
                    if i % 2 == 0:
                        ts.add("BACKGROUND", (0, i + 2), (-1, i + 2), colors.lightgrey)
            tt.setStyle(ts)
            elements.append(tt)

            # 順位分布
            df = pd.DataFrame(
                {
                    "1位率": [float(data[x + 1][6].replace("%", "")) for x in range(len(data) - 1)],
                    "2位率": [float(data[x + 1][8].replace("%", "")) for x in range(len(data) - 1)],
                    "3位率": [float(data[x + 1][10].replace("%", "")) for x in range(len(data) - 1)],
                    "4位率": [float(data[x + 1][12].replace("%", "")) for x in range(len(data) - 1)],
                }, index=[f"{str(data[x + 1][0])} - {str(data[x + 1][1])}" for x in range(len(data) - 1)]
            )

            imgdata = graphing_rank_distribution(df, f"順位分布 （ 区間 {title} ）")
            elements.append(Spacer(1, 5 * mm))
            elements.append(Image(imgdata, width=1200 * 0.5, height=800 * 0.5))

            # 通算ポイント推移
            data = get_count_moving(count)
            tmp_df = pd.DataFrame(data)
            df = pd.DataFrame()
            for i in sorted(tmp_df["interval"].unique().tolist()):
                list_data = tmp_df[tmp_df.interval == i]["point_sum"].to_list()
                game_count = tmp_df[tmp_df.interval == i]["total_count"].to_list()
                df[f"{min(game_count)} - {max(game_count)}"] = [None] * (count - len(list_data)) + list_data

            imgdata = graphing_total_points(df, f"通算ポイント推移（区間 {title}）", True)
            elements.append(Image(imgdata, width=1200 * 0.5, height=800 * 0.5))

            # 平均順位
            df = pd.DataFrame()
            for i in sorted(tmp_df["interval"].unique().tolist()):
                list_data = tmp_df[tmp_df.interval == i]["rank_avg"].to_list()
                game_count = tmp_df[tmp_df.interval == i]["total_count"].to_list()
                df[f"{min(game_count)} - {max(game_count)}"] = [None] * (count - len(list_data)) + list_data

            imgdata = graphing_mean_rank(df, f"平均順位推移（区間 {title}）", True)
            elements.append(Image(imgdata, width=1200 * 0.5, height=500 * 0.5))

            elements.append(PageBreak())

    return (elements)
