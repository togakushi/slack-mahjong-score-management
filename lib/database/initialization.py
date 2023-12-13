import sqlite3

from lib.function import global_value as g

def initialization_resultdb():
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)

    resultdb.execute(
        """
        create table if not exists "member" (
            "id"        INTEGER,
            "name"      TEXT NOT NULL UNIQUE,
            "slack_id"  TEXT,
            "flying"    INTEGER DEFAULT 0,
            "reward"    INTEGER DEFAULT 0,
            "abuse"     INTEGER DEFAULT 0,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
        """
    )

    resultdb.execute(
        """
        create table if not exists "alias" (
            "name"      TEXT,
            "member"    TEXT NOT NULL,
            PRIMARY KEY("name")
        );
        """
    )

    resultdb.execute(
        """
        create table if not exists "result" (
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
        );
        """
    )

    resultdb.execute("drop view individual;")
    resultdb.execute(
        """
        create view if not exists individual as
            select
                datetime(playtime) as playtime,
                p1_name as name,
                p1_rpoint as rpoint,
                p1_rank as rank,
                p1_point as point,
                substr(
                    case when
                        time(playtime) between "00:00:00" and "11:59:59"
                            then date(playtime, "-1 days")
                            else date(playtime)
                    end, 1, 7
                ) as collection,
                rule_version
            from
                result
            union select 
                datetime(playtime),
                p2_name,
                p2_rpoint,
                p2_rank,
                p2_point,
                substr(
                    case when
                        time(playtime) between "00:00:00" and "11:59:59"
                            then date(playtime, "-1 days")
                            else date(playtime)
                    end, 1, 7
                ),
                rule_version
            from
                result
            union select
                datetime(playtime),
                p3_name,
                p3_rpoint,
                p3_rank,
                p3_point,
                substr(
                    case when
                        time(playtime) between "00:00:00" and "11:59:59"
                            then date(playtime, "-1 days")
                            else date(playtime)
                    end, 1, 7
                ),
                rule_version
            from
                result
            union select
                datetime(playtime),
                p4_name,
                p4_rpoint,
                p4_rank,
                p4_point,
                substr(
                    case when
                        time(playtime) between "00:00:00" and "11:59:59"
                            then date(playtime, "-1 days")
                            else date(playtime)
                    end, 1, 7
                ),
                rule_version
            from
                result
            ;
        """
    )

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0")
    data = ret.fetchall()

    if len(data) == 0:
        g.logging.info(f"ゲスト設定: {g.guest_name}")
        sql = "insert into member (id, name) values (0, ?)"
        resultdb.execute(sql, (g.guest_name,))
    elif data[0][1] != g.guest_name:
        g.logging.info(f"ゲスト修正: {data[0][1]} -> {g.guest_name}")
        sql = "update member set name=? where id=0"
        resultdb.execute(sql, (g.guest_name,))

    resultdb.commit()
    resultdb.close()
