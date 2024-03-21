import os
import sqlite3
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, TableStyle, LongTable, Image
from reportlab.platypus import Paragraph, PageBreak, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

import pandas as pd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.function as f
import lib.command.report._query as query
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def get_game_results(argument, command_option, flag = "M"):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = query.for_report_personal_data(argument, command_option, flag = flag)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # --- データ収集
    results = [
        [
            "",
            "ゲーム数",
            "累積\nポイント",
            "平均\nポイント",
            "1位", "",
            "2位", "",
            "3位", "",
            "4位", "",
            "平均\n順位",
            "トビ", "",
            "最初", "最後",
        ]
    ]

    for row in rows.fetchall():
        if row["ゲーム数"] == 0:
            break

        results.append(
            [
                row["集計"],
                row["ゲーム数"],
                str(row["累積ポイント"]).replace("-", "▲") + "pt",
                str(row["平均ポイント"]).replace("-", "▲") + "pt",
                row["1位"], f"{row['1位率']:.2f}%",
                row["2位"], f"{row['2位率']:.2f}%",
                row["3位"], f"{row['3位率']:.2f}%",
                row["4位"], f"{row['4位率']:.2f}%",
                f"{row['平均順位']:.2f}",
                row["トビ"], f"{row['トビ率']:.2f}%",
                row["最初"], row["最後"],
            ]
        )
    g.logging.info(f"return record: {len(results)}")
    resultdb.close()

    if len(results) == 1: # ヘッダのみ
        return(False)

    return(results)


def get_count_results(argument, command_option, game_count):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = query.for_report_count_data(argument, command_option, game_count)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # --- データ収集
    results = [
        [
            "開始",
            "終了",
            "ゲーム数",
            "累積\nポイント",
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
                str(row["累積ポイント"]).replace("-", "▲") + "pt",
                str(row["平均ポイント"]).replace("-", "▲") + "pt",
                row["1位"], f"{row['1位率']:.2f}%",
                row["2位"], f"{row['2位率']:.2f}%",
                row["3位"], f"{row['3位率']:.2f}%",
                row["4位"], f"{row['4位率']:.2f}%",
                f"{row['平均順位']:.2f}",
                row["トビ"], f"{row['トビ率']:.2f}%",
            ]
        )
    g.logging.info(f"return record: {len(results)}")
    resultdb.close()

    if len(results) == 1: # ヘッダのみ
        return(False)

    return(results)


def gen_pdf(argument, command_option):
    _, target_player, _, command_option = f.common.argument_analysis(argument, command_option)

    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)

    # --- レポート作成
    pdf_path = os.path.join(os.path.realpath(os.path.curdir), "Results.pdf")
    pdfmetrics.registerFont(TTFont("ReportFont", font_path))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize = landscape(A4),
    )

    style = ParagraphStyle(
        name = "Normal",
        fontName = "ReportFont",
        fontSize = 14,
    )

    style_title = ParagraphStyle(
        name = "Title",
        fontName = "ReportFont",
        fontSize = 24,
    )

    # グラフフォント設定
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    elements = []
    # 全件のデータ
    tmp_data = get_game_results(argument, command_option, flag = "A") # todo: 0件のときはFalseが返る
    if not tmp_data:
        return(False)

    total_game_count = int(tmp_data[1][1]) # トータルゲーム数
    game_first = tmp_data[1][15] # 最初のゲーム
    game_last = tmp_data[1][16] # 最後のゲーム
    g.logging.info(f"total: {total_game_count}, first: {game_first}, last: {game_last}")

    # タイトル
    elements.append(Paragraph(f"成績レポート：{target_player[0]}", style_title))
    elements.append(Spacer(1,10*mm))
    elements.append(Paragraph(f"集計期間：{game_first} - {game_last}", style))
    elements.append(Spacer(1,3*mm))
    elements.append(Paragraph(f"作成日：{datetime.now().strftime('%Y-%m-%d')}", style))
    elements.append(Spacer(1,15*mm))
    elements.append(PageBreak())

    # トータル
    elements.append(Paragraph("全期間", style))
    elements.append(Spacer(1,5*mm))
    data = []
    for x in range(len(tmp_data)):
        data.append(tmp_data[x][1:15])
    tt = LongTable(data, repeatRows = 1)
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
    ]))
    elements.append(tt)

    imgdata = BytesIO()
    gdata = pd.DataFrame({
        "順位分布": [
            float(data[1][4].replace("%", "")),
            float(data[1][6].replace("%", "")),
            float(data[1][8].replace("%", "")),
            float(data[1][10].replace("%", "")),
            ],
        }, index = ["1位率", "2位率", "3位率", "4位率"]
    )
    gdata.plot(
        kind = "pie",
        y = "順位分布",
        labels = None,
        figsize = (8, 6),
        fontsize = 14,
        autopct = "%.2f%%",
    )
    plt.title("順位分布", fontsize = 18)
    plt.ylabel(None)
    plt.legend(list(gdata.index), bbox_to_anchor = (0.5, -0.1), loc = "lower center", ncol = 4, fontsize = 12)
    plt.savefig(imgdata, format = "jpg")

    elements.append(Spacer(1,5*mm))
    elements.append(
        Image(imgdata,
        width = 800 * 0.5,
        height = 600 * 0.5,
    ))
    plt.close()
    elements.append(PageBreak())

    # 月別集計
    elements.append(Paragraph("月別集計", style))
    elements.append(Spacer(1,5*mm))
    data = []
    tmp_data = get_game_results(argument, command_option, flag = "M") # todo: 0件のときはFalseが返る
    for x in range(len(tmp_data)):
        data.append(tmp_data[x][:15])

    tt = LongTable(data, repeatRows = 1)
    tt.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ('SPAN', (4, 0), (5, 0)),
        ('SPAN', (6, 0), (7, 0)),
        ('SPAN', (8, 0), (9, 0)),
        ('SPAN', (10, 0), (11, 0)),
        ('SPAN', (13, 0), (14, 0)),
    ]))
    elements.append(tt)
    elements.append(Spacer(1,10*mm))

    imgdata = BytesIO()
    gdata = pd.DataFrame({
        "1位率": [float(data[x + 1][5].replace("%", "")) for x in range(len(data) - 1)],
        "2位率": [float(data[x + 1][7].replace("%", "")) for x in range(len(data) - 1)],
        "3位率": [float(data[x + 1][9].replace("%", "")) for x in range(len(data) - 1)],
        "4位率": [float(data[x + 1][11].replace("%", "")) for x in range(len(data) - 1)],
        }, index = [data[x + 1][0] for x in range(len(data) - 1)]
    )

    gdata.plot(
        kind = "bar",
        stacked = True,
        figsize = (12, 7),
        fontsize = 14,
    )
    for ax in plt.gcf().get_axes():
        ax.set_axisbelow(True)
        plt.grid(axis="y")
    plt.title("順位分布(月別)", fontsize = 18)
    plt.xticks(rotation = 45)
    plt.legend(bbox_to_anchor = (0.5, 0), loc = "lower center", ncol = 4, fontsize = 12)
    plt.savefig(imgdata, format = "jpg")

    elements.append(Spacer(1,5*mm))
    elements.append(
        Image(imgdata,
        width = 1200 * 0.5,
        height = 700 * 0.5,
    ))
    plt.close()
    elements.append(PageBreak())

    # 年別集計
    elements.append(Paragraph("年別集計", style))
    elements.append(Spacer(1,5*mm))
    data = []
    tmp_data = get_game_results(argument, command_option, flag = "Y") # todo: 0件のときはFalseが返る
    for x in range(len(tmp_data)):
        data.append(tmp_data[x][:15])

    tt = LongTable(data, repeatRows = 1)
    tt.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ('SPAN', (4, 0), (5, 0)),
        ('SPAN', (6, 0), (7, 0)),
        ('SPAN', (8, 0), (9, 0)),
        ('SPAN', (10, 0), (11, 0)),
        ('SPAN', (13, 0), (14, 0)),
    ]))
    elements.append(tt)
    elements.append(Spacer(1,10*mm))

    imgdata = BytesIO()
    gdata = pd.DataFrame({
        "1位率": [float(data[x + 1][5].replace("%", "")) for x in range(len(data) - 1)],
        "2位率": [float(data[x + 1][7].replace("%", "")) for x in range(len(data) - 1)],
        "3位率": [float(data[x + 1][9].replace("%", "")) for x in range(len(data) - 1)],
        "4位率": [float(data[x + 1][11].replace("%", "")) for x in range(len(data) - 1)],
        }, index = [data[x + 1][0] for x in range(len(data) - 1)]
    )

    gdata.plot(
        kind = "bar",
        stacked = True,
        figsize = (12, 7),
        fontsize = 14,
    )
    for ax in plt.gcf().get_axes():
        ax.set_axisbelow(True)
        plt.grid(axis="y")
    plt.title("順位分布(年別)", fontsize = 18)
    plt.xticks(rotation = 45)
    plt.legend(bbox_to_anchor = (0.5, 0), loc = "lower center", ncol = 4, fontsize = 12)
    plt.savefig(imgdata, format = "jpg")

    elements.append(Spacer(1,5*mm))
    elements.append(
        Image(imgdata,
        width = 1200 * 0.5,
        height = 700 * 0.5,
    ))
    plt.close()
    elements.append(PageBreak())

    # 区間集計
    if total_game_count > 100:
        elements.append(Paragraph("区間集計(短期)", style))
        elements.append(Spacer(1,5*mm))
        data = get_count_results(argument, command_option, 80) # todo: 0件のときはFalseが返る
        tt = LongTable(data, repeatRows = 1)
        tt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ('SPAN', (5, 0), (6, 0)),
            ('SPAN', (7, 0), (8, 0)),
            ('SPAN', (9, 0), (10, 0)),
            ('SPAN', (11, 0), (12, 0)),
            ('SPAN', (14, 0), (15, 0)),
        ]))
        elements.append(tt)
        elements.append(Spacer(1,10*mm))

        gdata = pd.DataFrame({
            "1位率": [float(data[x + 1][6].replace("%", "")) for x in range(len(data) - 1)],
            "2位率": [float(data[x + 1][8].replace("%", "")) for x in range(len(data) - 1)],
            "3位率": [float(data[x + 1][10].replace("%", "")) for x in range(len(data) - 1)],
            "4位率": [float(data[x + 1][12].replace("%", "")) for x in range(len(data) - 1)],
            }, index = [data[x + 1][0] for x in range(len(data) - 1)]
        )

        imgdata = BytesIO()
        gdata.plot(
            kind = "bar",
            stacked = True,
            figsize = (12, 6),
            fontsize = 14,
        )
        for ax in plt.gcf().get_axes():
            ax.set_axisbelow(True)
            plt.grid(axis="y")
        plt.title("順位分布(区間 短期)", fontsize = 18)
        plt.legend(bbox_to_anchor = (0.5, 0), loc = "lower center", ncol = 4, fontsize = 12)
        plt.savefig(imgdata, format = "jpg")

        elements.append(Spacer(1,5*mm))
        elements.append(
            Image(imgdata,
            width = 1200 * 0.5,
            height = 600 * 0.5,
        ))
        plt.close()
        elements.append(PageBreak())

    if total_game_count > 240:
        elements.append(Paragraph("区間集計(中期)", style))
        elements.append(Spacer(1,5*mm))
        data = get_count_results(argument, command_option, 200) # todo: 0件のときはFalseが返る
        tt = LongTable(data, repeatRows = 1)
        tt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ('SPAN', (5, 0), (6, 0)),
            ('SPAN', (7, 0), (8, 0)),
            ('SPAN', (9, 0), (10, 0)),
            ('SPAN', (11, 0), (12, 0)),
            ('SPAN', (14, 0), (15, 0)),
        ]))
        elements.append(tt)
        elements.append(Spacer(1,10*mm))

        gdata = pd.DataFrame({
            "1位率": [float(data[x + 1][6].replace("%", "")) for x in range(len(data) - 1)],
            "2位率": [float(data[x + 1][8].replace("%", "")) for x in range(len(data) - 1)],
            "3位率": [float(data[x + 1][10].replace("%", "")) for x in range(len(data) - 1)],
            "4位率": [float(data[x + 1][12].replace("%", "")) for x in range(len(data) - 1)],
            }, index = [data[x + 1][0] for x in range(len(data) - 1)]
        )

        imgdata = BytesIO()
        gdata.plot(
            kind = "bar",
            stacked = True,
            figsize = (12, 5),
            fontsize = 14,
        )
        for ax in plt.gcf().get_axes():
            ax.set_axisbelow(True)
            plt.grid(axis="y")
        plt.title("順位分布(区間 中期)", fontsize = 18)
        plt.legend(bbox_to_anchor = (0.5, 0), loc = "lower center", ncol = 4, fontsize = 12)
        plt.savefig(imgdata, format = "jpg")

        elements.append(Spacer(1,5*mm))
        elements.append(
            Image(imgdata,
            width = 1200 * 0.5,
            height = 500 * 0.5,
        ))
        plt.close()
        elements.append(PageBreak())

    if total_game_count > 500:
        elements.append(Paragraph("区間集計(長期)", style))
        elements.append(Spacer(1,5*mm))
        data = get_count_results(argument, command_option, 400) # todo: 0件のときはFalseが返る
        tt = LongTable(data, repeatRows = 1)
        tt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "ReportFont", 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ('SPAN', (5, 0), (6, 0)),
            ('SPAN', (7, 0), (8, 0)),
            ('SPAN', (9, 0), (10, 0)),
            ('SPAN', (11, 0), (12, 0)),
            ('SPAN', (14, 0), (15, 0)),
        ]))
        elements.append(tt)
        elements.append(Spacer(1,10*mm))

        gdata = pd.DataFrame({
            "1位率": [float(data[x + 1][6].replace("%", "")) for x in range(len(data) - 1)],
            "2位率": [float(data[x + 1][8].replace("%", "")) for x in range(len(data) - 1)],
            "3位率": [float(data[x + 1][10].replace("%", "")) for x in range(len(data) - 1)],
            "4位率": [float(data[x + 1][12].replace("%", "")) for x in range(len(data) - 1)],
            }, index = [data[x + 1][0] for x in range(len(data) - 1)]
        )

        imgdata = BytesIO()
        gdata.plot(
            kind = "bar",
            stacked = True,
            figsize = (12, 5),
            fontsize = 14,
        )
        for ax in plt.gcf().get_axes():
            ax.set_axisbelow(True)
            plt.grid(axis="y")
        plt.title("順位分布(区間 長期)", fontsize = 18)
        plt.legend(bbox_to_anchor = (0.5, 0), loc = "lower center", ncol = 4, fontsize = 12)
        plt.savefig(imgdata, format = "jpg")

        elements.append(Spacer(1,5*mm))
        elements.append(
            Image(imgdata,
            width = 1200 * 0.5,
            height = 500 * 0.5,
        ))
        plt.close()

    doc.build(elements)

    return(pdf_path)
