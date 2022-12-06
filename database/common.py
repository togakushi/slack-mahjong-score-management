import function as f
from function import global_value as g


def select_table(cur, command_option):
    ret = cur.execute(
        "SELECT playtime, seat, player, rpoint, rank FROM 'gameresults';"
    )

    data = {}
    count = 0
    wind = ("東家", "南家", "西家", "北家")

    for row in ret.fetchall():
        if g.args.std:
            print(row)

        if not count in data:
            data[count] = {}

        data[count]["日付"] = row["playtime"]
        data[count][wind[row["seat"]]] = {
            "name": row["player"],
            "rpoint": row["rpoint"],
            "rank": row["rank"],
            "point": f.score.CalculationPoint(row["rpoint"], row["rank"]),
        }

        if row["seat"] == 3:
            count += 1
    
    if g.args.debug:
        print(data)

    return(data)
