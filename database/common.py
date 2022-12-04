import function as f
import command as c
from function import global_value as g


def select_table(cur, command_option):
    ret = cur.execute(\
        "SELECT playtime, seat, player, rpoint, rank FROM 'gameresults';"
    )

    data = {}
    count = 0
    wind = ["東家", "南家", "西家", "北家"]

    for row in ret.fetchall():
        if not count in data:
            data[count] = {}

        data[count]["日付"] = row[0]
        data[count][wind[row[1]]] = {
            "name": c.member.NameReplace(row[2], command_option),
            "rpoint": row[3],
            "rank": row[4],
            "point": f.score.CalculationPoint(row[3], row[4]),
        }

        if row[1] == 3:
            count += 1

    for i in range(len(data)):
        guest_count = 0
        for x in wind:
            if g.guest_name in data[i][x]["name"]:
                guest_count += 1
        g.logging.info(f"{i}: {data[i]} ({guest_count})")
    
    return(data)
