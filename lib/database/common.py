import os
import shutil
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def game_count(argument, command_option, cur):
    """
    指定条件を満たすゲーム数をカウントする

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    cur : object
        カーソル

    Returns
    -------
    game_count : int
        ゲーム数
    """

    prams = f.configure.get_parameters(argument, command_option)
    sql = """
        select
            count() as count
        from (
            select
                playtime
            from
                individual_results
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[target_player] and name in (:player_list) -- 対象プレイヤー
            group by
                playtime
            order by
                playtime desc
            --[recent] limit :target_count
        )
    """

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
    if prams["player_name"]:
        sql = sql.replace("--[target_player] ", "")

    if prams["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {prams}") # type: ignore

    rows = cur.execute(sql, prams)
    game_count = rows.fetchone()[0]

    return(int(game_count))


def ExsistRecord(ts):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    row = resultdb.execute("select ts from result where ts=?", (ts,))
    line = len(row.fetchall())
    resultdb.close()

    if line:
        return(True)
    return(False)


def resultdb_insert(msg, ts):
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
        array[i1]["rank"], array[i1]["point"] = f.score.calculation_point(rpoint_data, rpoint_data[i2], i2)

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.execute(d.sql_result_insert, (
        ts, datetime.fromtimestamp(float(ts)),
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit, g.rule_version, "",
        )
    )
    resultdb.commit()
    g.logging.notice(f"{ts}: {array}") # type: ignore
    resultdb.close()


def resultdb_update(msg, ts):
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
        array[i1]["rank"], array[i1]["point"] = f.score.calculation_point(rpoint_data, rpoint_data[i2], i2)

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.execute(d.sql_result_update, (
        array["p1"]["name"], array["p1"]["str"], array["p1"]["rpoint"], array["p1"]["rank"], array["p1"]["point"],
        array["p2"]["name"], array["p2"]["str"], array["p2"]["rpoint"], array["p2"]["rank"], array["p2"]["point"],
        array["p3"]["name"], array["p3"]["str"], array["p3"]["rpoint"], array["p3"]["rank"], array["p3"]["point"],
        array["p4"]["name"], array["p4"]["str"], array["p4"]["rpoint"], array["p4"]["rank"], array["p4"]["point"],
        deposit,
        ts
        )
    )
    resultdb.commit()
    g.logging.notice(f"{ts}: {array}") # type: ignore
    resultdb.close()


def resultdb_delete(ts):
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.execute(d.sql_result_delete, (ts,))
    resultdb.execute(d.sql_remarks_delete_all, (ts,))
    resultdb.commit()
    g.logging.notice(f"{ts}") # type: ignore
    resultdb.close()


def database_backup():
    backup_dir = g.config["database"].get("backup_dir", "")
    fname = os.path.splitext(g.database_file)[0]
    fext = os.path.splitext(g.database_file)[1]
    bktime = datetime.now().strftime('%Y%m%d-%H%M%S')
    bkfname = os.path.join(backup_dir, f"{fname}_{bktime}{fext}")

    if not backup_dir: # バックアップ設定がされていない場合は何もしない
        return("")

    if not os.path.isdir(backup_dir): # バックアップディレクトリ作成
        try:
            os.mkdir(backup_dir)
        except:
            g.logging.error("Database backup directory creation failed !!!")
            return("\nバックアップ用ディレクトリ作成の作成に失敗しました。")

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.database_file, bkfname)
        g.logging.notice(f"database backup: {bkfname}") # type: ignore
        return("\nデータベースをバックアップしました。")
    except:
        g.logging.error("Database backup failed !!!")
        return("\nデータベースのバックアップに失敗しました。")
