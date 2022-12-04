import csv

from dateutil.relativedelta import relativedelta

import command as c
import function as f
from function import global_value as g


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


def csv_export(argument, command_option):
    command_option["playername_replace"] = False
    command_option["unregistered_replace"] = False

    target_days, target_player, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)
    rule_version = g.config["mahjong"].get("rule_version", "未定義")

    g.logging.info(f"[export] {command_option}")
    results = c.search.getdata(command_option)

    # csv出力 
    command_option["playername_replace"] = True
    filename = "{}-{}.csv".format(
        starttime.strftime("%Y%m%d"), endtime.strftime("%Y%m%d"))

    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        game_day = ""
        game_count = 0
        for i in range(len(results)):
            if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
                previous_game_day = (results[i]["日付"] + relativedelta(hours = -12)).strftime("%Y-%m-%d")
                if game_day == previous_game_day:
                    game_count += 1
                else:
                    game_day = previous_game_day
                    game_count = 1

                for seki, seki_no in [("東家", 0), ("南家", 1), ("西家", 2), ("北家", 3)]:
                    raw_name = results[i][seki]["name"]
                    player = c.member.NameReplace(raw_name, command_option)
                    gestflg = 0 if c.member.ExsistPlayer(player) else 1

                    writer.writerow([
                        game_day,
                        game_count,
                        results[i]["日付"].strftime("%Y-%m-%d %H:%M:%S"),
                        seki_no,
                        player,
                        eval(results[i][seki]["rpoint"]),
                        results[i][seki]["rank"],
                        gestflg,
                        rule_version,
                        raw_name,
                        "",
                    ])

    g.logging.info(f"[export] done -> {filename}")
    return(filename)