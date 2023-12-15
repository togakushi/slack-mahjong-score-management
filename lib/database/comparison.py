import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def slackpost(client, channel, event_ts, argument, command_option):
    """
    データ突合の実施、その結果をslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される

    command_option : dict
        コマンドオプション
    """

    # slackのログを取得
    slack_data = slack_search(command_option)
    if slack_data == None:
        return

    # データベースからデータを取得
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    fts = list(slack_data.keys())[0] # slackのログの先頭の時刻
    db_data = databese_search(cur, fts.split(".")[0] + ".0")
    if db_data == None:
        return

    # 突合処理
    mismatch, missing, delete = data_comparison(cur, slack_data, db_data, command_option)
    g.logging.info(f"mismatch:{mismatch}, missing:{missing}, delete:{delete}")
    msg = f"*【データ突合】*\n\t不一致： {mismatch}件\n\t取りこぼし： {missing}件\n\t削除漏れ： {delete}件\n"

    # 素点合計の再チェック
    msg2 =""
    for i in slack_data.keys():
        rpoint_data =[eval(slack_data[i][1]), eval(slack_data[i][3]), eval(slack_data[i][5]), eval(slack_data[i][7])]
        deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
        if not deposit == 0:
            msg2 += "\t{}\t供託：{}\n\t[{} {}][{} {}][{} {}][{} {}]\n\n".format(
                datetime.fromtimestamp(float(i)).strftime('%Y/%m/%d %H:%M:%S'), deposit,
                slack_data[i][0], slack_data[i][1], slack_data[i][2], slack_data[i][3],
                slack_data[i][4], slack_data[i][5], slack_data[i][6], slack_data[i][7],
            )
    if msg2:
        msg2 = "\n*【素点合計不一致】*\n" + msg2

    f.slack_api.post_message(client, channel, msg + msg2, event_ts)

    resultdb.commit()
    resultdb.close()


def data_comparison(cur, slack_data, db_data, command_option):
    mismatch = 0
    missing = 0
    delete = 0

    slack_data2 = []
    for key in slack_data.keys():
        skey1 = key
        skey2 = key.split(".")[0] + ".0"
        slack_data2.append(skey2)

        flg = False
        if skey1 in db_data.keys():
            if slack_data[key] == db_data[skey1]:
                continue
            else:
                flg = True
                skey = skey1

        if skey2 in db_data.keys():
            if slack_data[key] == db_data[skey2]:
                continue
            else:
                flg = True
                skey = skey2

        if flg:
            mismatch += 1
            #更新
            g.logging.info(f"[mismatch]: {skey}")
            g.logging.info(f" * [slack]: {slack_data[key]}")
            g.logging.info(f" * [   db]: {db_data[skey]}")
            db_update(cur, skey, slack_data[key], command_option)
            continue

        #追加
        missing += 1
        g.logging.info(f"[missing ]: {key}, {slack_data[key]}")
        db_insert(cur, key, slack_data[key], command_option)

    for key in db_data.keys():
        skey1 = key
        skey2 = key.split(".")[0] + ".0"
        if skey1 in slack_data.keys():
            continue
        if skey2 in slack_data2:
            continue

        # 削除
        delete += 1
        g.logging.info(f"[delete  ]: {key}, {db_data[key]}")
        db_delete(cur, key)

    return(mismatch, missing, delete)


def slack_search(command_option):
    """
    過去ログからスコアを検索して返す

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    data : dict
        検索した結果
    """

    keyword = g.config["search"].get("keyword", "終局")
    channel = g.config["search"].get("channel", "#麻雀部")
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効
    g.logging.info(f"query:'{keyword} in:{channel}' {command_option}")

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

    data = {}
    for i in range(len(matches)):
        if "blocks" in matches[i]:
            ts = matches[i]["ts"]
            if "elements" in matches[i]["blocks"][0]:
                tmp_msg = ""
                elements = matches[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = c.search.pattern(tmp_msg)
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
                    data[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7]]

    # slackのログに記録が1件もない場合は何もしない
    if len(data) == 0:
        return(None)
    else:
        return(data)


def databese_search(cur, first_ts = False):
    """
    データベースからスコアを検索して返す

    Parameters
    ----------
    cur: obj
        データベースのカーソル

    first_ts: float
        検索を開始する時刻

    Returns
    -------
    data : dict
        検索した結果
    """
    
    if not first_ts:
        return(None)

    data ={}
    rows = cur.execute(f"select * from result where ts >= ?", (first_ts,))
    for row in rows.fetchall():
        ts = row["ts"]
        data[ts] = []
        data[ts].append(row["p1_name"])
        data[ts].append(row["p1_str"])
        data[ts].append(row["p2_name"])
        data[ts].append(row["p2_str"])
        data[ts].append(row["p3_name"])
        data[ts].append(row["p3_str"])
        data[ts].append(row["p4_name"])
        data[ts].append(row["p4_str"])

    return(data)


def db_update(cur, ts, msg, command_option): # 突合処理専用
    # ポイント計算
    rpoint_data =[eval(msg[1]), eval(msg[3]), eval(msg[5]), eval(msg[7])]
    deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
    array = {"p1": {}, "p2": {}, "p3": {}, "p4": {}}
    for i1, i2 in ("p1",0),("p2",1),("p3",2),("p4",3):
        array[i1]["name"] = c.NameReplace(msg[i2 * 2], command_option, False)
        array[i1]["str"] = msg[i2 * 2 + 1]
        array[i1]["rpoint"] = rpoint_data[i2]
        array[i1]["rank"], array[i1]["point"] = f.CalculationPoint2(rpoint_data, rpoint_data[i2], i2)

    cur.execute(g.sql_result_update, (
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit,
        ts,
        )
    )


def db_insert(cur, ts, msg, command_option): # 突合処理専用
    # ポイント計算
    rpoint_data =[eval(msg[1]), eval(msg[3]), eval(msg[5]), eval(msg[7])]
    deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
    array = {"p1": {}, "p2": {}, "p3": {}, "p4": {}}
    for i1, i2 in ("p1",0),("p2",1),("p3",2),("p4",3):
        array[i1]["name"] = c.NameReplace(msg[i2 * 2], command_option, False)
        array[i1]["str"] = msg[i2 * 2 + 1]
        array[i1]["rpoint"] = rpoint_data[i2]
        array[i1]["rank"], array[i1]["point"] = f.CalculationPoint2(rpoint_data, rpoint_data[i2], i2)

    cur.execute(g.sql_result_insert, (
        ts, datetime.fromtimestamp(float(ts)),
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit, g.rule_version, "",
        )
    )


def db_delete(cur, ts): # 突合処理専用
    cur.execute(g.sql_result_delete, (ts,))
