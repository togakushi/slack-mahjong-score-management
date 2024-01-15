import os
import math
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.command as c
import lib.function as f
import lib.database as d
import lib.command.report._query as query
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]
    
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    # --- データ取得
    ret = d.query_count_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    total_game_count = rows.fetchone()[0]
    if command_option["stipulated"] == 0:
        command_option["stipulated"] = math.ceil(total_game_count * command_option["stipulated_rate"]) + 1

    ret = query.select_personal_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    results = {}
    playtime = []
    for row in rows.fetchall():
        name = row["プレイヤー"]
        results[name] = dict(row)
        results[name].update({"プレイヤー": c.NameReplace(name, command_option, add_mark = True)})
        playtime.append(row["first_game"])
        playtime.append(row["last_game"])
        # 描写しないカラムを削除
        results[name].pop("first_game")
        results[name].pop("last_game")
        results[name].pop("並び変え用カラム")
        g.logging.trace(f"{row['プレイヤー']}: {results[name]}")
    g.logging.info(f"return record: {len(results)}")

    resultdb.close()

    if len(results) == 0:
        return(False)

    # --- グラフフォント設定
    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname = font_path)
    plt.rcParams["font.family"] = font_prop.get_name()
    plt.rcParams["font.size"] = 6

    column_labels = list(results[list(results.keys())[0]].keys())
    column_color = ["#000080" for i in column_labels]

    cell_param = []
    cell_color = []
    line_count = 0
    for x in results.keys():
        line_count += 1
        cell_param.append([results[x][y] for y in column_labels])
        if int(line_count % 2):
            cell_color.append(["#ffffff" for i in column_labels])
        else:
            cell_color.append(["#dddddd" for i in column_labels])

    report_file_path = os.path.join(os.path.realpath(os.path.curdir), "report2.png")
    fig = plt.figure(figsize = (8, (len(results) * 0.2) + 0.8), dpi = 200, tight_layout = True)
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title("個人成績", fontsize = 12)

    tb = plt.table(
        colLabels = column_labels,
        colColours = column_color,
        cellText = cell_param,
        cellColours = cell_color,
        loc = "center",
    )

    tb.auto_set_font_size(False)
    for i in range(len(column_labels)):
        tb[0, i].set_text_props(color = "#FFFFFF", weight = "bold")
    for i in range(len(results.keys()) + 1):
        tb[i, 0].set_text_props(ha = "center")

    # 追加テキスト
    remark_text =  f.remarks(command_option).replace("\t", "")
    add_text = "[集計期間：{} - {}] [総ゲーム数：{}] [規定数：{} ゲーム以上] {}".format(
        min(playtime).replace("-", "/"),
        max(playtime).replace("-", "/"),
        total_game_count,
        command_option["stipulated"],
        f"[{remark_text}]" if remark_text else "",
    )

    fig.text(0.01, 0.01, # 表示位置(左下0,0 右下0,1)
        add_text,
        transform = fig.transFigure,
        fontsize = 6,
    )
    fig.savefig(report_file_path)

    return(report_file_path)
