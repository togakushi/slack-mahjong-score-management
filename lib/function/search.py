import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
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
    rows = resultdb.execute("select * from result where rule_version=?;", (g.rule_version,))

    for row in rows.fetchall():
        data[count] = {
            "日付": datetime.fromtimestamp(float(row["ts"])),
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
            data[count][wind]["name"] = c.NameReplace(data[count][wind]["name"], command_option)

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


def slack_search(keyword, channel):
    """
    過去ログからキーワードを検索して返す

    Parameters
    ----------
    keyword : text
        検索キーワード

    channel : text
        チャンネルID

    Returns
    -------
    matches : dict
        検索した結果
    """

    g.logging.info(f"query:'{keyword} in:{channel}'")

    ### データ取得 ###
    response = g.webclient.search_messages(
        query = f"{keyword} in:{channel}",
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query = f"{keyword} in:{channel}",
            sort = "timestamp",
            sort_dir = "asc",
            count = 100,
            page = p
        )
        matches += response["messages"]["matches"] # 2ページ目以降

    return(matches)


def game_result(data, command_option):
    """
    slackの検索ログからゲームの結果を返す

    Parameters
    ----------
    data : dict
        slackの検索ログ

    command_option : dict
        検索オプション

    Returns
    -------
    matches : dict
        検索した結果
    """

    result = {}
    for i in range(len(data)):
        if "blocks" in data[i]:
            ts = data[i]["ts"]
            if "elements" in data[i]["blocks"][0]:
                tmp_msg = ""
                elements = data[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = f.search.pattern(tmp_msg)
                if msg:
                    p1_name = c.NameReplace(msg[0], command_option, add_mark = False)
                    p2_name = c.NameReplace(msg[2], command_option, add_mark = False)
                    p3_name = c.NameReplace(msg[4], command_option, add_mark = False)
                    p4_name = c.NameReplace(msg[6], command_option, add_mark = False)
                    #g.logging.info("post data:[{} {} {}][{} {} {}][{} {} {}][{} {} {}]".format(
                    #    "東家", p1_name, msg[1], "南家", p2_name, msg[3],
                    #    "西家", p3_name, msg[5], "北家", p4_name, msg[7],
                    #    )
                    #)
                    result[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7]]

    if len(result) == 0:
        return(None)
    else:
        return(result)
