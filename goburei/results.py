import re
import datetime

from function import global_value as g
from function import common
from function import message
from function import slack_api
from goburei import search


# イベントAPI
@g.app.message(re.compile(r"^御無礼成績"))
def handle_goburei_results_evnts(client, context, body):
    v = body["event"]["text"].split()

    if not re.match(r"^御無礼成績$", v[0]):
        return

    title, msg = getdata(v[1:], name_replace = True, guest_skip = True)
    if title or msg:
        slack_api.post_text(client, context.channel_id, title, msg)
    else:
        slack_api.post_message(client, context.channel_id, message.invalid_argument())


def getdata(keyword, name_replace = True, guest_skip = True):
    """
    各プレイヤーの累積ポイントを取得

    Parameters
    ----------
    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default True
        2ゲスト戦の除外

    keyword : list
        slackから受け取った引数
        集計対象の期間などが指定される

    Returns
    -------
    title : str
        slackにpostするタイトル

    msg : text
        slackにpostする内容
    """

    starttime = False
    endtime = False
    target_day = []

    for i in keyword:
        if re.match(r"^(今月|先月|先々月|全部)$", i):
            starttime, endtime = common.scope_coverage(i)
        if re.match(r"^[0-9]{8}$", common.ZEN2HAN(i)):
            target_day.append(common.ZEN2HAN(i))

    if len(keyword) == 0:
        starttime, endtime = common.scope_coverage("今月")
    if len(target_day) == 1:
        starttime, endtime = common.scope_coverage(target_day[0])
    if len(target_day) >= 2:
        starttime, dummy = common.scope_coverage(min(target_day))
        dummy, endtime = common.scope_coverage(max(target_day))
    if not (starttime or endtime):
        return(False, False)

    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)

    r = {}
    game_count = 0
    tobi_count = 0
    first_game = False
    last_game = False

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            if not first_game:
                first_game = results[i]["日付"]
            last_game = results[i]["日付"]
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
    header = "## 名前 : 累計 (平均) / 順位分布 (平均) / トビ ##\n"

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

    footer = "-" * 5 + "\n"
    footer += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"最初のゲーム：{first_game.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"最後のゲーム：{last_game.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"ゲーム回数： {game_count} 回 / トバされた人（延べ）： {tobi_count} 人\n"
    if not name_replace:
        footer += "特記事項：名前ブレ修正なし\n"

    if not msg:
        msg = "御無礼なし"

    return("", header + msg + footer)