import logging
import math
import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f
from lib.database import query

mlogger = logging.getLogger("matplotlib")
mlogger.setLevel(logging.WARNING)


def plot():
    plt.close()
    # 検索動作を合わせる
    g.opt.guest_skip = g.opt.guest_skip2

    game_info = d.aggregate.game_info()
    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    resultdb.row_factory = sqlite3.Row

    # --- データ取得
    if g.opt.stipulated == 0:
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)  # 更新

    sql = query.report.results_list()
    rows = resultdb.execute(sql, g.prm.to_dict())

    results = {}
    for row in rows.fetchall():
        name = row["name"]
        results[name] = dict(row)
        if g.opt.individual:
            results[name].update(
                {"name": c.member.NameReplace(name, add_mark=True)}
            )
        logging.trace(f"{row['name']}: {results[name]}")  # type: ignore
    logging.info(f"return record: {len(results)}")

    resultdb.close()

    if len(results) == 0:
        return (False)

    # --- グラフフォント設定
    f.common.graph_setup(plt, fm)
    plt.rcParams["font.size"] = 6

    # 見出し設定
    if g.opt.individual:
        graph_title = "個人成績"
        column_name = "プレイヤー名"
    else:  # チーム集計
        graph_title = "チーム成績"
        column_name = "チーム名"

    # 非表示項目
    for x in results.keys():
        if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
            results[x].pop("トビ")

    # 色彩設定
    match (plt.rcParams["text.color"], plt.rcParams["figure.facecolor"]):
        case text_color, bg_color if text_color == "black" and bg_color == "white":
            line_color1 = "#ffffff"
            line_color2 = "#dddddd"
        case text_color, bg_color if text_color == "white" and bg_color == "black":
            line_color1 = "#000000"
            line_color2 = "#111111"
        case _:
            line_color1 = plt.rcParams["figure.facecolor"]
            line_color2 = plt.rcParams["figure.facecolor"]

    column_labels = list(results[list(results.keys())[0]].keys())
    column_color = ["#000080" for i in column_labels]

    cell_param = []
    cell_color = []
    line_count = 0
    for x in results.keys():
        line_count += 1
        cell_param.append([results[x][y] for y in column_labels])
        if int(line_count % 2):
            cell_color.append([line_color1 for i in column_labels])
        else:
            cell_color.append([line_color2 for i in column_labels])

    report_file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}.png" if g.opt.filename else "report.png"
    )

    fig = plt.figure(
        figsize=(8, (len(results) * 0.2) + 0.8),
        dpi=200, tight_layout=True
    )
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title(graph_title, fontsize=12)

    tb = plt.table(
        colLabels=[column_name] + column_labels[1:],
        colColours=column_color,
        cellText=cell_param,
        cellColours=cell_color,
        loc="center",
    )

    tb.auto_set_font_size(False)
    tb.auto_set_column_width(range(len(column_labels)))
    for i in range(len(column_labels)):
        tb[0, i].set_text_props(color="#FFFFFF", weight="bold")
        for j in range(len(results.keys()) + 1):
            tb[j, i].set_text_props(ha="center")

    # 追加テキスト
    remark_text = f.message.remarks().strip()
    if g.opt.search_word:
        add_text = "[集計範囲：{} - {}] [総ゲーム数：{}] [規定数：{} ゲーム以上] {}".format(
            game_info["first_comment"],
            game_info["last_comment"],
            game_info["game_count"],
            g.opt.stipulated,
            f"[{remark_text}]" if remark_text else "",
        )
    else:
        add_text = "[集計範囲：{} - {}] [総ゲーム数：{}] [規定数：{} ゲーム以上] {}".format(
            game_info["first_game"],
            game_info["last_game"],
            game_info["game_count"],
            g.opt.stipulated,
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
