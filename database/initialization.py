import csv
import sqlite3


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
            'gestflg'       INTEGER,\
            'rule_version'  TEXT,\
            'raw_name'      TEXT,\
            'comment'       TEXT,\
            PRIMARY KEY('serial')\
        );"
    )


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
        "gestflg",
        "rule_version",
        "raw_name",
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
                        'gestflg',\
                        'rule_version',\
                        'raw_name',\
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
                        :gestflg,\
                        :rule_version,\
                        :raw_name,\
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