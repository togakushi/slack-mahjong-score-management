import sqlite3

from lib.function import global_value as g

def initialization_resultdb():
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)

    resultdb.execute(
        """create table if not exists "member" (
            "id"        INTEGER,
            "name"      TEXT NOT NULL UNIQUE,
            "slack_id"  TEXT,
            "flying"    INTEGER DEFAULT 0,
            "reward"    INTEGER DEFAULT 0,
            "abuse"     INTEGER DEFAULT 0,
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
        g.logging.info(f"ゲスト設定: {g.guest_name}")
        sql = "insert into member (id, name) values (?, ?)"
        resultdb.execute(sql, [0, g.guest_name])
    elif data[0][1] != g.guest_name:
        g.logging.info(f"ゲスト修正: {data[0][1]} -> {g.guest_name}")
        sql = "update member set name=? where id=0"
        resultdb.execute(sql, [g.guest_name])

    resultdb.commit()
    resultdb.close()
