import logging
import math
import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import global_value as g
from lib import database as d
from lib import function as f

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)


def plot():
    plt.close()
    # 検索動作を合わせる
    g.opt.guest_skip = g.opt.guest_skip2

    # --- データ取得
    game_info = d.aggregate.game_info()

    if g.opt.stipulated == 0:
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)  # 更新

    df = d.aggregate.personal_report()

    if df.empty:
        return (False)

    # 見出し設定
    if g.opt.individual:
        title = "個人成績一覧"
        df = df.rename(columns={"name": "プレイヤー名"})
    else:  # チーム集計
        title = "チーム成績一覧"
        df = df.rename(columns={"name": "チーム名"})

    # 非表示項目
    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        df = df.drop(columns=["トビ"])
    if "トビ" in g.cfg.dropitems.report:
        df = df.drop(columns=["トビ"])
    if "役満" in g.cfg.dropitems.report:
        df = df.drop(columns=["役満和了"])
    if "役満和了" in g.cfg.dropitems.report:
        df = df.drop(columns=["役満和了"])

    match g.opt.format:
        case "text" | "txt":
            file_path = text_generation(df)
        case "csv":
            file_path = csv_generation(df)
        case _:
            file_path = graph_generation(game_info, df, title)

    return (file_path)


def graph_generation(game_info, df, title):
    # --- グラフフォント設定
    report_file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "report.png"
    )

    f.common.graph_setup(plt, fm)
    plt.rcParams["font.size"] = 6

    # 色彩設定
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

    fig = plt.figure(
        figsize=(8, (len(df) * 0.2) + 0.8),
        dpi=200, tight_layout=True
    )
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
    remark_text = f.message.remarks(True) + f.message.search_word(True)
    add_text = "[{}] [総ゲーム数： {}] {}".format(
        f.message.item_search_range(None, "time").strip(),
        game_info["game_count"],
        f"[{remark_text}]" if remark_text else "",
    )

    fig.text(
        0.01, 0.01,  # 表示位置(左下0,0 右下0,1)
        add_text,
        transform=fig.transFigure,
        fontsize=6,
    )
    fig.savefig(report_file_path)
    plt.close()

    return (report_file_path)


def text_generation(df):
    report_file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.txt" if g.opt.filename else "report.txt"
    )

    fmt = [""]  # index分
    for x in df.columns:
        match x:
            case "平均順位":
                fmt.append(".2f")
            case _:
                fmt.append("")

    df.to_markdown(report_file_path, tablefmt="outline", floatfmt=fmt)

    return (report_file_path)


def csv_generation(df):
    report_file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.csv" if g.opt.filename else "report.csv"
    )

    df.to_csv(report_file_path)

    return (report_file_path)
