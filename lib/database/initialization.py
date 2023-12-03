import csv
import sqlite3

from lib.function import global_value as g

def create_table(cur):
    cur.execute(\
        "CREATE TABLE IF NOT EXISTS 'gameresults' (\
            'serial'        INTEGER NOT NULL UNIQUE,\
            'game_day'      TIMESTAMP,\
            'game_count'    INTEGER,\
            'playtime'      TIMESTAMP,\
            'seat'          INTEGER,\
            'player'        TEXT,\
            'rpoint'        INTEGER,\
            'rank'          INTEGER,\
            'rule_version'  TEXT,\
            'comment'       TEXT,\
            PRIMARY KEY('serial')\
        );"
    )


def initialization_resultdb():
    resultdb = sqlite3.connect(g.database_path, detect_types = sqlite3.PARSE_DECLTYPES)

    resultdb.execute(
        """create table if not exists "member" (
            "id"        INTEGER,
            "name"      TEXT NOT NULL,
            "slack_id"  INTEGER,
            "flg1"      INTEGER DEFAULT 0,
            "flg2"      INTEGER DEFAULT 0,
            "flg3"      INTEGER DEFAULT 0,
            PRIMARY KEY("id" AUTOINCREMENT)
        );"""
    )

    resultdb.execute(
        """create table if not exists "alias" (
            "name"      TEXT,
            "member"    TEXT NOT NULL,
            PRIMARY KEY("name")
        );"""
    )

    resultdb.execute(
        """create table if not exists "result" (
            "ts"            TEXT,
            "playtime"      TIMESTAMP UNIQUE,
            "p1_name"       TEXT NOT NULL,
            "p1_str"        TEXT NOT NULL,
            "p1_rpoint"     INTEGER,
            "p1_rank"       INTEGER,
            "p1_point"      INTEGER,
            "p2_name"       TEXT NOT NULL,
            "p2_str"        TEXT NOT NULL,
            "p2_rpoint"     INTEGER,
            "p2_rank"       INTEGER,
            "p2_point"      INTEGER,
            "p3_name"       TEXT NOT NULL,
            "p3_str"        TEXT NOT NULL,
            "p3_rpoint"     INTEGER,
            "p3_rank"       INTEGER,
            "p3_point"      INTEGER,
            "p4_name"       TEXT NOT NULL,
            "p4_str"        TEXT NOT NULL,
            "p4_rpoint"     INTEGER,
            "p4_rank"       INTEGER,
            "p4_point"      INTEGER,
            "deposit"       INTEGER,
            "rule_version"  TEXT,
            "comment"       TEXT,
            PRIMARY KEY("ts")
        );"""
    )

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0")
    data = ret.fetchall()

    if len(data) == 0:
        print("ゲスト設定", g.guest_name)
        sql = "insert into member (id, name) values (?, ?)"
        resultdb.execute(sql, [0, g.guest_name])
    elif data[0][1] != g.guest_name:
        print("ゲスト修正", data[0][1], "->", g.guest_name)
        sql = "update member set name=? where id=0"
        resultdb.execute(sql, [g.guest_name])

    resultdb.commit()
    resultdb.close()

def csv_import(cur, csvfile):
    csv_header = [
        "serial",
        "game_day",
        "game_count",
        "playtime",
        "seat",
        "player",
        "rpoint",
        "rank",
        "rule_version",
        "comment",
    ]

    with open(csvfile) as f:
        count = 0 # インポートしたレコード数
        for row in csv.DictReader(f, csv_header):
            try:
                cur.execute(\
                    "INSERT INTO 'gameresults' (\
                        'serial',\
                        'game_day',\
                        'game_count',\
                        'playtime',\
                        'seat',\
                        'player',\
                        'rpoint',\
                        'rank',\
                        'rule_version',\
                        'comment'\
                    ) VALUES (\
                        :serial,\
                        :game_day,\
                        :game_count,\
                        :playtime,\
                        :seat,\
                        :player,\
                        :rpoint,\
                        :rank,\
                        :rule_version,\
                        :comment\
                    );",
                    row
                )

                count += 1
                if g.args.std:
                    print("import ->", row)
            except:
                pass
                
    return(count)
