import csv

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def CalculationPoint(rpoint, rank):
    """
    順位点を計算して獲得ポイントを返す

    Parameters
    ----------
    rpoint : int
        素点

    rank : int
        着順（1位→1、2位→2、、、）

    Returns
    -------
    float : float
        獲得ポイント
    """

    p = g.config["mahjong"].getint("point", 250)
    r = g.config["mahjong"].getint("return", 300)
    u = g.config["mahjong"].get("rank_point", "30,10,-10,-30")

    oka = (r - p) * 4 / 10
    uma = [int(x) for x in u.split(",")]
    uma[0] = uma[0] + oka
    point = (rpoint - r) / 10 + uma[rank - 1]

    return(float(f"{point:>.1f}"))

def CalculationPoint2(rpoint_data, rpoint, seat):
    """
    素点データと獲得素点から獲得ポイントと順位を返す
    """

    temp_data = []
    correction = [0.000004, 0.000003, 0.000002, 0.000001]
    for i in range(len(rpoint_data)):
        temp_data.append(rpoint_data[i] + correction[i])

    temp_data.sort(reverse = True)
    rank = temp_data.index(rpoint + correction[seat]) + 1
    point = CalculationPoint(rpoint, rank)

    return(rank, point)


def csv_export(argument, command_option):
    command_option["unregistered_replace"] = False

    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)
    rule_version = g.config["mahjong"].get("rule_version", "未定義")

    g.logging.info(f"[export] {command_option}")
    results = c.search.getdata(command_option)

    # csv出力 
    filename = "{}-{}.csv".format(
        starttime.strftime("%Y%m%d"), endtime.strftime("%Y%m%d"))

    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        game_day = ""
        game_count = 0
        for i in results.keys():
            if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
                previous_game_day = (results[i]["日付"] + relativedelta(hours = -12)).strftime("%Y-%m-%d")
                if game_day == previous_game_day:
                    game_count += 1
                else:
                    game_day = previous_game_day
                    game_count = 1

                for wind, wind_no in [("東家", 0), ("南家", 1), ("西家", 2), ("北家", 3)]:
                    writer.writerow([
                        f"{game_day}{game_count:02}{wind_no}".replace("-", ""),
                        game_day,
                        game_count,
                        results[i]["日付"].strftime("%Y-%m-%d %H:%M:%S"),
                        wind_no,
                        results[i][wind]["name"],
                        eval(results[i][wind]["rpoint"]),
                        results[i][wind]["rank"],
                        rule_version,
                        "",
                    ])

    g.logging.info(f"[export] done -> {filename}")
    return(filename)
