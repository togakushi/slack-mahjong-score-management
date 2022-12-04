import csv
import sqlite3


def create_table(cur):
    cur.execute(\
        "CREATE TABLE IF NOT EXISTS 'gameresults' (\
            'id'            INTEGER NOT NULL UNIQUE,\
            'game_day'      TIMESTAMP,\
            'game_count'    INTEGER,\
            'playtime'      TIMESTAMP,\
            'seat'          INTEGER,\
            'player'          TEXT,\
            'rpoint'        INTEGER,\
            'rank'          INTEGER,\
            'gestflg'       INTEGER,\
            'rule_version'  TEXT,\
            'raw_name'       TEXT,\
            'comment'       TEXT,\
            PRIMARY KEY('id' AUTOINCREMENT)\
        );"
    )


def csv_import(cur, csvfile):
    csv_header = [
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
        for row in csv.DictReader(f, csv_header):
            print(row)
            cur.execute(\
                "INSERT INTO 'gameresults' (\
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