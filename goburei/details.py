import re
import datetime

from function import global_value as g
from function import common
from function import slack_api
from goburei import member


def getdata(opt):
    if len(opt) == 1:
        pname = member.NameReplace(opt[0], guest = False)
        if pname in g.player_list.sections():
            results = search.getdata(name_replace = True, guest_skip = False)
            starttime, endtime = common.scope_coverage("今月")

            msg1 = starttime.strftime(f"*【%Y年%m月の個人成績(※2ゲスト戦含む)】*\n")
            msg2 = starttime.strftime(f"\n*【%Y年%m月の戦績】*\n")

            point = 0
            count_rank = [0, 0, 0, 0]
            count_tobi = 0
            count_win = 0
            count_lose = 0
            count_draw = 0

            for i in range(len(results)):
                if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
                    for seki in ("東家", "南家", "西家", "北家"):
                        if pname == results[i][seki]["name"]:
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
            msg1 += "プレイヤー名： {}\n対戦数： {} 半荘 ({} 勝 {} 敗 {} 分)\n".format(
                pname, sum(count_rank), count_win, count_lose, count_draw,
            )
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
            msg2 += datetime.datetime.now().strftime(f"\n_(%Y/%m/%d %H:%M:%S 集計)_")
        else:
            msg1 = f"「{pname}」は登録されていません。"
            msg2 = ""
    else:
        msg1 = "使い方： /goburei details <登録名>"
        msg2 = ""

    return(msg1 + msg2)
