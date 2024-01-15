import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.command.report._query as query
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = query.select_game_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # --- データ収集
    results = {}
    for row in rows.fetchall():
        results[row["集計月"]] = dict(row)
        g.logging.trace(f"{row['集計月']}: {results[row['集計月']]}")
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

    report_file_path = os.path.join(os.path.realpath(os.path.curdir), "report.png")
    fig = plt.figure(figsize = (6, (len(results) * 0.2) + 0.8), dpi = 200, tight_layout = True)
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title("月別ゲーム統計", fontsize = 12)
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
    add_text = "[検索範囲：{} - {}] [特記：すべてのゲーム結果を含む]".format(
        ret["starttime"].strftime('%Y/%m/%d %H:%M'),
        ret["endtime"].strftime('%Y/%m/%d %H:%M'),
    )

    fig.text(0.01, 0.02, # 表示位置(左下0,0 右下0,1)
        add_text,
        transform = fig.transFigure,
        fontsize = 6,
    )

    fig.savefig(report_file_path)

    return(report_file_path)
