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

    keyword = g.config["search"].get("keyword", "終局")
    pattern1 = re.compile(rf"^{keyword}([^0-9+-]+[0-9+-]+){{4}}$")
    pattern2 = re.compile(rf"([^0-9+-]+[0-9+-]+){{4}}{keyword}$")

    # 全角マイナス符号(0x2212)は半角に置換
    text = "".join(text.split()).replace(chr(0x2212),'-')
    if pattern1.search(text) or pattern2.search(text):
        ret = re.sub(rf"^{keyword}|{keyword}$", "", text)
        ret = re.sub(rf"([^0-9+-]+)([0-9+-]+)" * 4, r"\1 \2 \3 \4 \5 \6 \7 \8", ret).split()

    return(ret if "ret" in locals() else False)


def game_select(starttime, endtime, target_player, target_count, command_option):
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

    command_option : dict
        コマンドオプション

    Returns
    -------
    ret : dict
        条件に合致したゲーム結果
    """

    g.logging.info(f"date range: {starttime} {endtime}, target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    if target_count != 0 and len(target_player) == 0: # プレイヤー指定なしの直近N回
        sql = "select * from (select * from result where rule_version=? order by playtime desc limit ?) order by playtime"
        placeholder = [g.rule_version, target_count]
    elif target_count != 0 and len(target_player) != 0: # プレイヤー指定ありの直近N回
        sql = "select * from (select * from result where rule_version=? and ("
        sql += " or".join([" ? in (p1_name, p2_name, p3_name, p4_name)" for i in target_player])
        sql += ") order by playtime desc limit ?) order by playtime"
        placeholder = [g.rule_version] + target_player + [target_count]
    elif target_count == 0 and len(target_player) != 0: # プレイヤー指定あり
        sql = "select * from result where rule_version=? and playtime between ? and ? and ("
        sql += " or".join([" ? in (p1_name, p2_name, p3_name, p4_name)" for i in target_player]) + ")"
        placeholder = [g.rule_version, starttime, endtime] + target_player
    else: # 条件なし
        sql = "select * from result where rule_version=? and playtime between ? and ?"
        placeholder = [g.rule_version, starttime, endtime]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")
    rows = resultdb.execute(sql, placeholder)

    data = {}
    count = 0
    for row in rows.fetchall():
        p1_name = c.NameReplace(row["p1_name"], command_option, add_mark = True)
        p2_name = c.NameReplace(row["p2_name"], command_option, add_mark = True)
        p3_name = c.NameReplace(row["p3_name"], command_option, add_mark = True)
        p4_name = c.NameReplace(row["p4_name"], command_option, add_mark = True)
        guest_count = [p1_name, p2_name, p3_name, p4_name].count(g.guest_name)

        if command_option["guest_skip"] and guest_count >= 2:
            g.logging.trace(f"2ゲスト戦除外: {row['ts']}, {p1_name}, {p2_name}, {p3_name}, {p4_name}")
        else:
            data[count] = {
                "日付": datetime.fromtimestamp(float(row["ts"])),
                "東家": {"name": p1_name, "rpoint": row["p1_rpoint"], "rank": row["p1_rank"], "point": row["p1_point"]},
                "南家": {"name": p2_name, "rpoint": row["p2_rpoint"], "rank": row["p2_rank"], "point": row["p2_point"]},
                "西家": {"name": p3_name, "rpoint": row["p3_rpoint"], "rank": row["p3_rank"], "point": row["p3_point"]},
                "北家": {"name": p4_name, "rpoint": row["p4_rpoint"], "rank": row["p4_rank"], "point": row["p4_point"]},
            }
            g.logging.trace(f"{count}: {data[count]}")
            count += 1

    g.logging.info(f"return record: {len(data)}")
    resultdb.close()
    return(data)


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
            if data[i]["user"] in g.ignore_userid: # 除外ユーザからのポストは集計対象から外す
                g.logging.info(f"skip: {data[i]}")
                continue

            ts = data[i]["ts"]
            if "elements" in data[i]["blocks"][0]:
                tmp_msg = ""
                elements = data[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = f.pattern(tmp_msg)
                if msg:
                    p1_name = c.NameReplace(msg[0], command_option)
                    p2_name = c.NameReplace(msg[2], command_option)
                    p3_name = c.NameReplace(msg[4], command_option)
                    p4_name = c.NameReplace(msg[6], command_option)
                    result[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7]]
                    g.logging.trace(result[ts])

    if len(result) == 0:
        return(None)
    else:
        return(result)
