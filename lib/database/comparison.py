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

    event_ts: text
        スレッドに返す場合の返し先

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される

    command_option : dict
        コマンドオプション
    """

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    # スコア突合
    count, msg, fts = score_comparison(command_option)

    # カウンター突合
    if fts: # slackからスコア記録のログが見つかった場合のみチェック
        counter_comparison(fts)

    g.logging.notice("mismatch:{}, missing:{}, delete:{}, invalid_score: {}".format(
        count["mismatch"],
        count["missing"],
        count["delete"],
        count["invalid_score"],
    ))

    ret = f"*【データ突合】*\n"
    ret += "＊ 不一致： {}件\n{}".format(count["mismatch"], msg["mismatch"])
    ret += "＊ 取りこぼし：{}件\n{}".format(count["missing"], msg["missing"])
    ret += "＊ 削除漏れ： {}件\n{}".format(count["delete"], msg["delete"])
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    f.slack_api.post_message(client, channel, ret, event_ts)


def score_comparison(command_option):
    """
    スコア突合
    """

    ret_msg = {"mismatch": "", "missing": "", "delete": "", "invalid_score": ""}
    count = {"mismatch": 0, "missing": 0, "delete": 0, "invalid_score": 0}
    fts = None # slackのログの先頭の時刻

    # slackからログを取得
    matches = c.search.slack_search(
        g.config["search"].get("keyword", "終局"),
        g.config["search"].get("channel", "#麻雀部"),
    )
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効
    slack_data = c.search.game_result(matches, command_option)
    if slack_data == None:
        return(count, ret_msg, fts)

    # データベースからデータを取得
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    fts = list(slack_data.keys())[0]
    db_data = database_search(cur, fts.split(".")[0] + ".0")
    if db_data == None:
        return(count, ret_msg, fts)

    # 突合処理
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
            count["mismatch"] += 1
            #更新
            g.logging.notice(f"mismatch: {skey}")
            g.logging.info(f"   * [slack]: {slack_data[key]}")
            g.logging.info(f"   * [   db]: {db_data[skey]}")
            ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(
                datetime.fromtimestamp(float(skey)).strftime('%Y/%m/%d %H:%M:%S'),
                textformat(db_data[skey]), textformat(slack_data[key]),
            )
            db_update(cur, skey, slack_data[key], command_option)
            continue

        #追加
        count["missing"] += 1
        g.logging.notice(f"missing: {key}, {slack_data[key]}")
        ret_msg["missing"] += "\t{} {}\n".format(
            datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
            textformat(slack_data[key])
         )
        db_insert(cur, key, slack_data[key], command_option)

    for key in db_data.keys():
        skey1 = key
        skey2 = key.split(".")[0] + ".0"
        if skey1 in slack_data.keys():
            continue
        if skey2 in slack_data2:
            continue

        # 削除
        count["delete"] += 1
        g.logging.notice(f"delete: {key}, {db_data[key]} (Only database)")
        ret_msg["delete"] += "\t{} {}\n".format(
            datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
            textformat(db_data[key])
         )
        db_delete(cur, key)

    # 素点合計の再チェック
    for i in slack_data.keys():
        rpoint_data =[eval(slack_data[i][1]), eval(slack_data[i][3]), eval(slack_data[i][5]), eval(slack_data[i][7])]
        deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
        if not deposit == 0:
            count["invalid_score"] += 1
            ret_msg["invalid_score"] += "\t{} [供託：{}]{}\n".format(
                datetime.fromtimestamp(float(i)).strftime('%Y/%m/%d %H:%M:%S'),
                deposit, textformat(slack_data[i])
            )

    resultdb.commit()
    resultdb.close()

    return(count, ret_msg, fts)


def database_search(cur, first_ts = False):
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


def textformat(text):
    """
    メッセージを整形する
    """

    ret = ""
    for i in range(0,len(text),2):
        ret += f"[{text[i]} {str(text[i + 1])}]"

    return(ret)


def counter_comparison(fts):
    """
    カウンター突合
    """

    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効
    slack_data = {}
    db_data = {}

    # slackからデータ取得
    matches = c.search.slack_search(
        g.commandword["count"],
        g.config["search"].get("channel", "#麻雀部"),
    )

    count = 0
    for i in range(len(matches)):
        event_ts = matches[i]["ts"]
        text = matches[i]["text"]
        permalink = matches[i]["permalink"]
        if permalink.split("?thread_ts=")[1:]:
            thread_ts = permalink.split("?thread_ts=")[1:][0]
        else:
            thread_ts = None

        if re.match(rf"^{g.commandword['count']}", text):
            if thread_ts:
                for name, val in zip(text.split()[1:][0::2], text.split()[1:][1::2]):
                    slack_data[count] = {
                        "thread_ts": thread_ts,
                        "event_ts": event_ts,
                        "name": name,
                        "matter": val,
                    }
                    g.logging.trace(f"slack: {slack_data[count]}")
                    count += 1

    slack_ts = set([slack_data[i]["event_ts"] for i in slack_data.keys()])

    # データベースからデータ取得
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    count = 0
    rows = cur.execute(f"select * from counter where thread_ts >= ?", (fts,))
    for row in rows.fetchall():
        db_data[count] = {
            "thread_ts": row["thread_ts"],
            "event_ts": row["event_ts"],
            "name": row["name"],
            "matter": row["matter"],
        }
        g.logging.trace(f"database: {db_data[count]}")
        count += 1

    db_ts = set([db_data[i]["event_ts"] for i in db_data.keys()])

    # 突合処理
    for x in slack_ts:
        check_data_src = []
        for i in slack_data.keys():
            if slack_data[i]["event_ts"] == x:
                check_data_src.append(slack_data[i])

        check_data_dst = []
        for i in db_data.keys():
            if db_data[i]["event_ts"] == x:
                check_data_dst.append(db_data[i])

        # スレッド元をデータベースから検索
        find_ts = []
        for i in check_data_src:
            rows = cur.execute("select ts from result where ts=?", (str(i["thread_ts"]),))
            for row in rows.fetchall():
                find_ts.append(row["ts"])

        if find_ts: # スレッド元がある
            if check_data_src == check_data_dst:
                continue
            else:
                cur.execute(g.sql_counter_delete_one, (str(x),))
                for update_data in check_data_src:
                    cur.execute(g.sql_counter_insert, (
                        update_data["thread_ts"],
                        update_data["event_ts"],
                        c.NameReplace(update_data["name"], command_option, add_mark = False),
                        update_data["matter"],
                    ))
                    g.logging.info(f"update: {update_data}")
        else: # スレッド元がないデータは不要
            cur.execute(g.sql_counter_delete_one, (str(x),))
            g.logging.info(f"delete: {x} (No thread origin)")

    for x in db_ts:
        if x not in slack_ts: # データベースにあってslackにない → 削除
            cur.execute(g.sql_counter_delete_one, (str(x),))
            g.logging.info(f"delete: {x} (Only database)")

    resultdb.commit()
    resultdb.close()
