import os
import math
import sqlite3

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g

mlogger = g.logging.getLogger("matplotlib")
mlogger.setLevel(g.logging.WARNING)


def plot(argument, command_option):
    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    params = f.configure.get_parameters(argument, command_option)
    sql = """
        select
            name as プレイヤー,
            count() as ゲーム数,
            replace(round(sum(point), 1), "-", "▲") as 累積ポイント,
            replace(round(avg(point), 1), "-", "▲") as 平均ポイント,
            printf("%3d (%7.2f%%)",
                count(rank = 1 or null),
                round(cast(count(rank = 1 or null) as real) / count() * 100, 2)
            ) as '1位',
            printf("%3d (%7.2f%%)",
                count(rank = 2 or null),
                round(cast(count(rank = 2 or null) as real) / count() * 100, 2)
            ) as '2位',
            printf("%3d (%7.2f%%)",
                count(rank = 3 or null),
                round(cast(count(rank = 3 or null) as real) / count() * 100, 2)
            ) as '3位',
            printf("%3d (%7.2f%%)",
                count(rank = 4 or null),
                round(cast(count(rank = 4 or null) AS real) / count() * 100, 2)
            ) as '4位',
            printf("%.2f", round(avg(rank), 2)) as 平均順位,
            printf("%3d (%7.2f%%)",
                count(rpoint < 0 or null),
                round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2)
            ) as トビ,
            printf("%3d (%7.2f%%)",
                ifnull(sum(gs_count), 0),
                round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2)
            ) as 役満和了,
            min(playtime) as first_game,
            max(playtime) as last_game,
            sum(point) as 並び変え用カラム
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                rpoint,
                rank,
                point,
                gs_count
            from
                individual_results
            left outer join
                (select thread_ts, name,count() as gs_count from remarks group by thread_ts, name) as remarks
                on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and individual_results.name in (:player_list) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            並び変え用カラム desc
    """

    if params["player_name"]:
        sql = sql.replace("--[player_name] ", "")

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")

    if params["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    # --- データ取得
    total_game_count = d.common.game_count(argument, command_option, cur)
    if command_option["stipulated"] == 0:
        command_option["stipulated"] = math.ceil(total_game_count * command_option["stipulated_rate"]) + 1
        params = f.configure.get_parameters(argument, command_option) # 更新

    rows = resultdb.execute(sql, params)

    results = {}
    playtime = []
    for row in rows.fetchall():
        name = row["プレイヤー"]
        results[name] = dict(row)
        results[name].update({"プレイヤー": c.member.NameReplace(name, command_option, add_mark = True)})
        playtime.append(row["first_game"])
        playtime.append(row["last_game"])
        # 描写しないカラムを削除
        results[name].pop("first_game")
        results[name].pop("last_game")
        results[name].pop("並び変え用カラム")
        g.logging.trace(f"{row['プレイヤー']}: {results[name]}") # type: ignore
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

    report_file_path = os.path.join(g.work_dir, "report2.png")
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
    remark_text = f.message.remarks(command_option).replace("\t", "")
    add_text = "[集計範囲：{} - {}] [総ゲーム数：{}] [規定数：{} ゲーム以上] {}".format(
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
    plt.close()

    return(report_file_path)
