import re
import datetime

from function import global_value as g
from function import common
from function import slack_api
from goburei import search
from goburei import member


def getdata(opt):
    """
    個人成績を集計して返す

    Parameters
    ----------
    opt : list
        解析対象のプレイヤー、集計期間

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    starttime = False
    endtime = False
    target_player = ""
    target_day = []
    option = []

    for i in opt:
        if member.ExsistPlayer(i):
            target_player = member.ExsistPlayer(i)
        if re.match(r"^(今月|先月|先々月|全部)$", i):
            starttime, endtime = common.scope_coverage(i)
        if re.match(r"^[0-9]{8}$", common.ZEN2HAN(i)):
            target_day.append(common.ZEN2HAN(i))
        if re.match(r"^(戦績)$", i):
            option.append(i)

    if not (starttime or endtime):
        if len(target_day) == 0:
            starttime, endtime = common.scope_coverage("今月")
            option.append("戦績")
        if len(target_day) == 1:
            starttime, endtime = common.scope_coverage(target_day[0])
        if len(target_day) >= 2:
            starttime, dummy = common.scope_coverage(min(target_day))
            dummy, endtime = common.scope_coverage(max(target_day))

    if target_player:
        results = search.getdata(name_replace = True, guest_skip = False)
 
        msg1 = f"*【個人成績】* (※2ゲスト戦含む)\n"
        msg2 = f"\n*【戦績】*\n"

        point = 0
        count_rank = [0, 0, 0, 0]
        count_tobi = 0
        count_win = 0
        count_lose = 0
        count_draw = 0

        for i in range(len(results)):
            if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
                for seki in ("東家", "南家", "西家", "北家"):
                    if target_player == results[i][seki]["name"]:
                        count_rank[results[i][seki]["rank"] -1] += 1
                        point += float(results[i][seki]["point"])
                        count_tobi += 1 if eval(results[i][seki]["rpoint"]) < 0 else 0
                        count_win += 1 if float(results[i][seki]["point"]) > 0 else 0
                        count_lose += 1 if float(results[i][seki]["point"]) < 0 else 0
                        count_draw += 1 if float(results[i][seki]["point"]) == 0 else 0
                        msg2 += "{}： {}位 {:>5}00点 ({:>+5.1f}) {}\n".format(
                            results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"),
                            results[i][seki]["rank"], eval(results[i][seki]["rpoint"]), float(results[i][seki]["point"]),
                            "※" if [results[i][x]["name"] for x in ("東家", "南家", "西家", "北家")].count("ゲスト１") >= 2 else "",
                        ).replace("-", "▲")

        msg1 += f"プレイヤー名： {target_player}\n"
        msg1 += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
        msg1 += f"対戦数： {sum(count_rank)} 半荘 ({count_win} 勝 {count_lose} 敗 {count_draw} 分)\n"

        if sum(count_rank) > 0:
            msg1 += "累積ポイント： {:+.1f}\n平均ポイント： {:+.1f}\n".format(
                point, point / sum(count_rank),
            ).replace("-", "▲")
            for i in range(4):
                msg1 += "{}位： {:2} 回 ({:.2%})\n".format(i + 1, count_rank[i], count_rank[i] / sum(count_rank))
            msg1 += "トビ： {} 回 ({:.2%})\n".format(count_tobi, count_tobi / sum(count_rank))
            msg1 += "平均順位： {:1.2f}\n".format(
                sum([count_rank[i] * (i + 1) for i in range(4)]) / sum(count_rank),
            )
        else:
            msg2 += f"記録なし\n"
    else:
        msg1 = f"集計対象プレイヤーが見つかりません。"
        msg2 = ""

    if not "戦績" in option:
        msg2 = ""

    return(msg1 + msg2)
