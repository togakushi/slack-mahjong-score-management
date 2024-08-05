import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.function as f
import lib.database as d
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    # --- データ取得
    params = f.configure.get_parameters(argument, command_option)
    results_df = d.aggregate.winner_report(argument, command_option)

    if len(results_df) == 0:
        return(False)

    results = {}
    for _,v in results_df.iterrows():
        results[v["collection"]] = {}
        results[v["collection"]]["集計月"] = v["collection"]
        for x in range(1,6):
            if type(v[f"name{x}"]) == str:
                results[v["collection"]][f"{x}位"] = "{} ({}pt)".format(
                    v[f"pname{x}"],
                    str("{:+}".format(v[f"point{x}"])).replace("-", "▲")
                )
            else:
                results[v["collection"]][f"{x}位"] = v[f"pname{x}"]

    # --- グラフ設定
    f.common.set_graph_font(plt, fm)
    plt.rcParams["font.size"] = 6
    report_file_path = os.path.join(g.work_dir,
        command_option["filename"] + ".png" if command_option["filename"] else "report.png"
    )

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

    fig = plt.figure(figsize = (6.5, (len(results) * 0.2) + 0.8), dpi = 200, tight_layout = True)
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title("成績上位者", fontsize = 12)

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
        for j in range(len(column_labels)):
            tb[i, j].set_text_props(ha = "center")

    # 追加テキスト
    remark_text = f.message.remarks(command_option).replace("\t", "")
    add_text = "[検索範囲：{} - {}] {} {}".format(
        params["starttime_hm"], params["endtime_hm"],
        f"[規定数：{command_option['stipulated']} ゲーム以上]" if command_option["stipulated"] != 0 else "",
        f"[{remark_text}]" if remark_text else "",
    )

    fig.text(0.01, 0.02, # 表示位置(左下0,0 右下0,1)
        add_text,
        transform = fig.transFigure,
        fontsize = 6,
    )

    fig.savefig(report_file_path)
    plt.close()

    return(report_file_path)
