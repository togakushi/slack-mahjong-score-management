import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.database as db
from lib.function import global_value as g


def pattern(text):
    """
    成績記録用フォーマットチェック

    Parameters
    ----------
    text : text
        slackにポストされた内容

    Returns
    -------
    ret : text / False
        フォーマットに一致すればスペース区切りの名前と素点のペア
    """

    keyword = g.config["search"].get("keyword", "御無礼")
    pattern1 = re.compile(rf"^{keyword}([^0-9+-]+[0-9+-]+){{4}}")
    pattern2 = re.compile(rf"([^0-9+-]+[0-9+-]+){{4}}{keyword}$")

    # 全角マイナス符号(0x2212)は半角に置換
    text = "".join(text.split()).replace(chr(0x2212),'-')
    if pattern1.search(text) or pattern2.search(text):
        ret = re.sub(rf"^{keyword}|{keyword}$", "", text)
        ret = re.sub(rf"([^0-9+-]+)([0-9+-]+)" * 4, r"\1 \2 \3 \4 \5 \6 \7 \8", ret).split()

    return(ret if "ret" in locals() else False)


def getdata(command_option):
    """
    成績データ取得

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    data : dict
        変換、修正後の成績データ
    """

    g.logging.info(f"command_option: {command_option}")

    data = {}
    count = 0

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute("select * from result;")

    for row in rows.fetchall():
        data[count] = {
            "日付": datetime.fromtimestamp(float(row["ts"])).replace(microsecond = 0),
            "東家": {"name": row["p1_name"], "rpoint": row["p1_rpoint"], "rank": row["p1_rank"], "point": row["p1_point"]},
            "南家": {"name": row["p2_name"], "rpoint": row["p2_rpoint"], "rank": row["p2_rank"], "point": row["p2_point"]},
            "西家": {"name": row["p3_name"], "rpoint": row["p3_rpoint"], "rank": row["p3_rank"], "point": row["p3_point"]},
            "北家": {"name": row["p4_name"], "rpoint": row["p4_rpoint"], "rank": row["p4_rank"], "point": row["p4_point"]},
        }
        count += 1

    resultdb.close()
    g.logging.info(f"return record: {len(data)}")

    # プレイヤー名の正規化、2ゲスト戦除外
    for count in list(data.keys()):
        guest_count = 0
        for wind in g.wind[0:4]:
            data[count][wind]["name"] = c.member.NameReplace(data[count][wind]["name"], command_option)

            if g.guest_name in data[count][wind]["name"]:
                guest_count += 1

        if command_option["guest_skip"] and guest_count >= 2:
            pop = data.pop(count)
            g.logging.trace(f"2ゲスト戦除外: {pop}")

    return(data)


def game_select(starttime, endtime, target_player, target_count, results):
    """
    集計対象のゲームを選択

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    target_count: int
        集計するゲーム数

    results: dict
        チェック対象の結果

    Returns
    -------
    ret : dict
        条件に合致したゲーム結果
    """

    ret = {}
    if target_count == 0:
        g.logging.info(f"date range: {starttime} {endtime} target_player: {target_player}")
        for i in results.keys():
            if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
                g.logging.trace(f"{i}: {results[i]}")
                ret[i] = results[i]
    else:
        g.logging.info(f"target_count: {target_count} target_player: {target_player}")
        chk_count = 0
        for i in sorted(results.keys(), reverse = True):
            if len(target_player) == 0:
                ret[i] = results[i]
                chk_count += 1
            else:
                for name in target_player:
                    if name in [results[i][wind]["name"] for wind in g.wind[0:4]]:
                        ret[i] = results[i]
                        chk_count += 1
                        break
            if chk_count >= target_count:
                break

        tmp = {}
        for i in sorted(ret):
            tmp[i] = ret[i]
        ret = tmp

    g.logging.info(f"return record: {len(ret)}")

    return(ret)
