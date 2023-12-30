import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.command as c
import lib.function as f
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def select_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            collection as 集計月,
            count() / 4 as ゲーム数,
            round(sum(point), 1) as 供託,
            count(rpoint < -1 or null) as "飛んだ人数(延べ)",
            round(cast(count(rpoint < -1 or null) as real) / cast(count() / 4 as real) * 100, 2) as トビ終了率,
            max(rpoint) as 最大素点,
            min(rpoint) as 最小素点
        from
            individual_results
        group by
            collection
        having
            collection like strftime("%Y-%%")
        order by
            collection desc
    """

    placeholder = []

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def plot(argument, command_option):

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = select_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # ---
    results = {}
    for row in rows.fetchall():
        results[row["集計月"]] = dict(row)
        g.logging.trace(f"{row['集計月']}: {results[row['集計月']]}")
    g.logging.info(f"return record: {len(results)}")

    print(">", results)

    font_path = os.path.join(os.path.realpath(os.path.curdir), "ipaexg.ttf") #IPAexGothic
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

    column_labels = [
        "集計月",
        "ゲーム数",
        "供託",
        "飛んだ人数(延べ)",
        "トビ終了率",
        "最大素点",
        "最小素点",
    ]

    param = []
    for x in results.keys():
        param.append([results[x][y] for y in column_labels])

    report_file_path = os.path.join(os.path.realpath(os.path.curdir), "report.png")
    fig = plt.figure(figsize=(6, 3), dpi=200)
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")
    plt.title("なにかのひょうをひょうじするてすと", fontsize = 12)
    plt.table(cellText = param, colLabels = column_labels, loc = "center")
    fig.savefig(report_file_path)
    plt.tight_layout()
    fig.tight_layout()

    return(report_file_path)
