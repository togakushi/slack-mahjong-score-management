import os
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.function as f
import lib.command as c
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
            collection as "集計月",
            printf("%s (%.1fpt)",
                max(case when rank = 1 then name end),
                max(case when rank = 1 then total end)
            ) as "1位",
            printf("%s (%.1fpt)",
                max(case when rank = 2 then name end),
                max(case when rank = 2 then total end)
            ) as "2位",
            printf("%s (%.1fpt)",
                max(case when rank = 3 then name end),
                max(case when rank = 3 then total end)
            ) as "3位",
            printf("%s (%.1fpt)",
                max(case when rank = 4 then name end),
                max(case when rank = 4 then total end)
            ) as "4位",
            printf("%s (%.1fpt)",
                max(case when rank = 5 then name end),
                max(case when rank = 5 then total end)
            ) as "5位"
        from (
            select
                collection,
                rank() over (partition by collection order by round(sum(point), 1) desc) as rank,
                name,
                round(sum(point), 1) as total
            from (
                select
                    collection,
                    --[unregistered_replace] case when guest = 0 then name else ? end as name, -- ゲスト有効
                    --[unregistered_not_replace] name, -- ゲスト無効
                    point
                from
                    individual_results
                where
                    rule_version = ?
                    and playtime between ? and ?
                    --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                    --[guest_skip] and guest = 0 -- ゲストなし
            )
            group by
                name, collection
        )
        group by
            collection
        order by
            collection desc
    """

    placeholder = [g.guest_name, g.rule_version, starttime, endtime]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))

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

    # --- データ取得
    ret = select_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    results = {}
    for row in rows.fetchall():
        results[row["集計月"]] = dict(row)
        for i in ("1位", "2位", "3位", "4位", "5位"):
            name, pt = row[i].split()
            name = c.NameReplace(name, command_option, add_mark = True)
            results[row["集計月"]].update({i: f"{name} {pt}"})
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

    report_file_path = os.path.join(os.path.realpath(os.path.curdir), "report3.png")
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
    remark_text =  f.remarks(command_option).replace("\t", "")
    add_text = "［検索期間：{} - {}］{}".format(
        ret["starttime"].strftime('%Y/%m/%d %H:%M'),
        ret["endtime"].strftime('%Y/%m/%d %H:%M'),
        f"［{remark_text}］" if remark_text else "",
    )

    fig.text(0.01, 0.02, # 表示位置(左下0,0 右下0,1)
        add_text,
        transform = fig.transFigure,
        fontsize = 6,
    )
    fig.savefig(report_file_path)

    return(report_file_path)
