#!/usr/bin/env python3
import os
import sqlite3

import lib.function as f
from lib.function import global_value as g


def name_normalization(player_list, name):
    if f.HIRA2KANA(name) in player_list:
        return(player_list[f.HIRA2KANA(name)])
    if f.KANA2HIRA(name) in player_list:
        return(player_list[f.KANA2HIRA(name)])

    return(name)


f.configure.parameter_load()

if os.path.exists(g.database_path):
    outputdb = sqlite3.connect(g.database_path, detect_types = sqlite3.PARSE_DECLTYPES)
    outputdb.row_factory = sqlite3.Row
    rows = outputdb.execute("select name, member from alias;")

    player_list = {}
    for row in rows.fetchall():
        if not row["member"] in player_list:
            player_list[row["member"]] = row["member"]
        if not row["name"] in player_list:
            player_list[row["name"]] = row["member"]

outputdb.close()

pointsum = g.config["mahjong"].getint("point", 250) * 4

if os.path.exists(g.args.input):
    inputdb = sqlite3.connect(g.args.input, detect_types = sqlite3.PARSE_DECLTYPES)
    inputdb.row_factory = sqlite3.Row
    rows = inputdb.execute("select playtime, seat, player, rpoint, rank, rule_version from 'gameresults';")

    id = 0
    post_data ={}

    for row in rows.fetchall():
        playtime = row["playtime"]
        rule_version = row["rule_version"]

        if row["seat"] == 0:
            rpoint_data = []
            p1_name = name_normalization(player_list, row["player"])
            p1_rpoint = row["rpoint"]
            rpoint_data.append(p1_rpoint)
        if row["seat"] == 1:
            p2_name = name_normalization(player_list, row["player"])
            p2_rpoint = row["rpoint"]
            rpoint_data.append(p2_rpoint)
        if row["seat"] == 2:
            p3_name = name_normalization(player_list, row["player"])
            p3_rpoint = row["rpoint"]
            rpoint_data.append(p3_rpoint)
        if row["seat"] == 3:
            p4_name = name_normalization(player_list, row["player"])
            p4_rpoint = row["rpoint"]
            rpoint_data.append(p4_rpoint)

            #
            deposit = pointsum - (int(p1_rpoint) + int(p2_rpoint) + int(p3_rpoint) + int(p4_rpoint))
            p1_rank, p1_point = f.CalculationPoint2(rpoint_data, int(p1_rpoint), 0)
            p2_rank, p2_point = f.CalculationPoint2(rpoint_data, int(p2_rpoint), 1)
            p3_rank, p3_point = f.CalculationPoint2(rpoint_data, int(p3_rpoint), 2)
            p4_rank, p4_point = f.CalculationPoint2(rpoint_data, int(p4_rpoint), 3)
            print("{} {} [{} {} {} {} {}][{} {} {} {} {}][{} {} {} {} {}][{} {} {} {} {}] {}".format(
                str(playtime.timestamp()), playtime,
                p1_name, str(p1_rpoint), p1_rpoint, p1_point, p1_rank,
                p2_name, str(p2_rpoint), p2_rpoint, p2_point, p2_rank,
                p3_name, str(p3_rpoint), p3_rpoint, p3_point, p3_rank,
                p4_name, str(p4_rpoint), p4_rpoint, p4_point, p4_rank,
                deposit,
                )
            )
            post_data[id] = [
                str(playtime.timestamp()), playtime,
                p1_name, str(p1_rpoint), p1_rpoint, p1_rank, p1_point,
                p2_name, str(p2_rpoint), p2_rpoint, p2_rank, p2_point,
                p3_name, str(p3_rpoint), p3_rpoint, p3_rank, p3_point,
                p4_name, str(p4_rpoint), p4_rpoint, p4_rank, p4_point,
                deposit, rule_version, "",
            ]
            id += 1

inputdb.close()

outputdb = sqlite3.connect(g.database_path, detect_types = sqlite3.PARSE_DECLTYPES)
for i in post_data:
    outputdb.execute(g.sql_result_insert, post_data[i])

outputdb.commit()
outputdb.close()
