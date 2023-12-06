#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g
from lib.database import comparison


def db_update(ts, msg):
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効

    # ポイント計算
    rpoint_data =[eval(msg[1]), eval(msg[3]), eval(msg[5]), eval(msg[7])]
    deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
    array = {"p1": {}, "p2": {}, "p3": {}, "p4": {}}
    for i1, i2 in ("p1",0),("p2",1),("p3",2),("p4",3):
        array[i1]["name"] = c.member.NameReplace(msg[i2 * 2], command_option, False)
        array[i1]["str"] = msg[i2 * 2 + 1]
        array[i1]["rpoint"] = rpoint_data[i2]
        array[i1]["rank"], array[i1]["point"] = f.CalculationPoint2(rpoint_data, rpoint_data[i2], i2)

    resultdb.execute(g.sql_result_update, (
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit,
        ts
        )
    )


def db_insert(ts, msg):
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効

    # ポイント計算
    rpoint_data =[eval(msg[1]), eval(msg[3]), eval(msg[5]), eval(msg[7])]
    deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
    array = {"p1": {}, "p2": {}, "p3": {}, "p4": {}}
    for i1, i2 in ("p1",0),("p2",1),("p3",2),("p4",3):
        array[i1]["name"] = c.member.NameReplace(msg[i2 * 2], command_option, False)
        array[i1]["str"] = msg[i2 * 2 + 1]
        array[i1]["rpoint"] = rpoint_data[i2]
        array[i1]["rank"], array[i1]["point"] = f.CalculationPoint2(rpoint_data, rpoint_data[i2], i2)

    resultdb.execute(g.sql_result_insert, (
        ts, datetime.fromtimestamp(float(ts)),
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit,
        g.config["mahjong"].get("rule_version", ""), ""
        )
    )


def db_delete(ts):
    resultdb.execute(g.sql_result_delete, (ts,))


def name_normalization(player_list, name):
    if f.HIRA2KANA(name) in player_list:
        return(player_list[f.HIRA2KANA(name)])
    if f.KANA2HIRA(name) in player_list:
        return(player_list[f.KANA2HIRA(name)])

    return(name)


# ---
f.configure.parameter_load()
command_option = f.configure.command_option_initialization("record")

# メンバーリスト
if os.path.exists(g.database_file):
    outputdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    outputdb.row_factory = sqlite3.Row
    rows = outputdb.execute("select name, member from alias;")

    player_list = {}
    for row in rows.fetchall():
        if not row["member"] in player_list:
            player_list[row["member"]] = row["member"]
        if not row["name"] in player_list:
            player_list[row["name"]] = row["member"]

outputdb.close()


# --- slack data
slack_data = comparison.slack_search(command_option)
fts = list(slack_data.keys())[0]


# --- database
db_data ={}
resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
resultdb.row_factory = sqlite3.Row

rows = resultdb.execute(f"select * from result where ts > ?", (fts.split(".")[0],))
for row in rows.fetchall():
    ts = row["ts"]
    db_data[ts] = []
    db_data[ts].append(row["p1_name"])
    db_data[ts].append(row["p1_str"])
    db_data[ts].append(row["p2_name"])
    db_data[ts].append(row["p2_str"])
    db_data[ts].append(row["p3_name"])
    db_data[ts].append(row["p3_str"])
    db_data[ts].append(row["p4_name"])
    db_data[ts].append(row["p4_str"])


# ---
mismatch = 0
missing = 0
delete = 0

slack_data2 = []
for key in slack_data.keys():
    skey = key
    if skey in db_data.keys():
        if slack_data[key] == db_data[skey]:
            continue
        else:
            mismatch += 1
            #更新
            print("[mismatch]:", key)
            print(" * [slack]:", slack_data[key])
            print(" * [   db]:", db_data[skey])
            db_update(skey, slack_data[key])
            continue

    skey = key.split(".")[0] + ".0"
    slack_data2.append(skey)
    if skey.split(".")[0]+".0" in db_data.keys():
        if slack_data[key] == db_data[skey]:
            continue
        else:
            mismatch += 1
            #更新
            print("[mismatch]:", key)
            print(" * [slack]:", slack_data[key])
            print(" * [db   ]:", db_data[skey])
            db_update(skey, slack_data[key])
            continue

    #追加
    missing += 1
    print("[missing ]:", key, slack_data[key])
    db_insert(key, slack_data[key])

for key in db_data.keys():
    skey1 = key
    skey2 = key.split(".")[0] + ".0"
    if skey1 in slack_data.keys():
        continue
    if skey2 in slack_data2:
        continue

    print("[delete  ]:", key, db_data[key])
    delete += 1
    db_delete(key)

print(f">>> mismatch:{mismatch}, missing:{missing}, delete:{delete}")
resultdb.commit()
resultdb.close()
