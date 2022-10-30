import re
import datetime

from function import global_value as g
from function import common
from function import slack_api
from goburei import search

### 御無礼成績 ###

# イベントAPI
@g.app.message(re.compile(r"^御無礼成績$"))
def handle_goburei_results_evnts(client, context):
    title, msg = getdata(name_replace = True, guest_skip = True)
    slack_api.post_text(client, context.channel_id, title, msg)


def getdata(name_replace = True, guest_skip = True):
    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)
    starttime, endtime = common.scope_coverage("今月")
    if name_replace:
        title = datetime.datetime.now().strftime("今月の成績 [%Y/%m/%d %H:%M:%S 集計]")
    else:
        title = datetime.datetime.now().strftime("今月の成績(名前ブレ修正なし) [%Y/%m/%d %H:%M 集計]")

    r = {}
    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            for seki in ("東家", "南家", "西家", "北家"): # 成績計算
                name = results[i][seki]["name"]
                if not name in r:
                    r[name] = {
                        "total": 0,
                        "rank": [0, 0, 0, 0],
                    }
                r[name]["total"] += round(results[i][seki]["point"], 2)
                r[name]["rank"][results[i][seki]["rank"] -1] += 1

    tmp_r = {}
    msg = ""
    for i in r.keys():
        tmp_r[i] = r[i]["total"]
    for u,p in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        msg += "{}{}： {:>+6.1f} ({:>+5.1f})".format(
            u, " " * (9 - common.len_count(u)),
            r[u]["total"],
            r[u]["total"] / sum(r[u]["rank"]),
        ).replace("-", "▲")
        msg += " / {}-{}-{}-{} ({:1.2f})\n".format(
            r[u]["rank"][0], r[u]["rank"][1], r[u]["rank"][2], r[u]["rank"][3],
            sum([r[u]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[u]["rank"]),
        )

    if not msg:
        msg = "御無礼なし"

    return(title, msg)