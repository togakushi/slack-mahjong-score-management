import re
import datetime

from function import global_value as g
from function import common
from function import slack_api
from goburei import search


# イベントAPI
@g.app.message(re.compile(r"^御無礼成績$"))
def handle_goburei_results_evnts(client, context):
    title, msg = getdata(name_replace = True, guest_skip = True)
    slack_api.post_text(client, context.channel_id, title, msg)


def getdata(name_replace = True, guest_skip = True):
    """
    各プレイヤーの累積ポイントを取得

    Parameters
    ----------
    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default True
        2ゲスト戦の除外

    Returns
    -------
    title : str
        slackにポストするタイトル

    msg : text
        slackにポストする内容
    """

    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)
    starttime, endtime = common.scope_coverage("今月")
    title = ""

    r = {}
    game_count = 0
    tobi_count = 0

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            game_count += 1
            for seki in ("東家", "南家", "西家", "北家"): # 成績計算
                name = results[i][seki]["name"]
                if not name in r:
                    r[name] = {
                        "total": 0,
                        "rank": [0, 0, 0, 0],
                        "tobi": 0,
                    }
                r[name]["total"] += round(results[i][seki]["point"], 2)
                r[name]["rank"][results[i][seki]["rank"] -1] += 1
                if eval(results[i][seki]["rpoint"]) < 0:
                    r[name]["tobi"] += 1
                    tobi_count += 1

    tmp_r = {}
    msg = ""
    header = "# 名前 : 積算 (平均) / 順位分布 (平均) / トビ\n"

    for i in r.keys():
        tmp_r[i] = r[i]["total"]
    for u,p in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        msg += "{}{}： {:>+6.1f} ({:>+5.1f})".format(
            u, " " * (9 - common.len_count(u)),
            r[u]["total"],
            r[u]["total"] / sum(r[u]["rank"]),
        ).replace("-", "▲")
        msg += " / {}-{}-{}-{} ({:1.2f}) / {}\n".format(
            r[u]["rank"][0], r[u]["rank"][1], r[u]["rank"][2], r[u]["rank"][3],
            sum([r[u]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[u]["rank"]),
            r[u]["tobi"],
        )

    footer = "\n" + "-" * 20 + "\n"
    footer += f"ゲーム数： {game_count} 回 / トバされた人： {tobi_count} 人\n"
    footer += f"集計期間：{starttime.strftime('%Y/%m/%d %H:%M')}  ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    if not name_replace:
        footer += "特記事項：名前ブレ修正なし\n"
    footer += datetime.datetime.now().strftime("集計日時：%Y/%m/%d %H:%M:%S")

    if not msg:
        msg = "御無礼なし"

    return(title, header + msg + footer)