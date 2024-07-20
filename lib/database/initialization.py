import sqlite3

from lib.function import global_value as g

def initialization_resultdb():
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    # --- メンバー登録テーブル
    resultdb.execute(
        """
        create table if not exists "member" (
            "id"        INTEGER,
            "name"      TEXT NOT NULL UNIQUE,
            "slack_id"  TEXT,
            "team_id"   INTEGER,
            "flying"    INTEGER DEFAULT 0,
            "reward"    INTEGER DEFAULT 0,
            "abuse"     INTEGER DEFAULT 0,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
        """
    )

    # 追加したカラム
    rows = resultdb.execute("pragma table_info(member);")
    for row in rows.fetchall():
        if row["name"] == "team_id":
            break
    else:
        resultdb.execute("alter table member add column team_id INTEGER;")

    # --- 別名定義テーブル
    resultdb.execute(
        """
        create table if not exists "alias" (
            "name"      TEXT,
            "member"    TEXT NOT NULL,
            PRIMARY KEY("name")
        )
        """
    )

    # --- チーム定義テーブル
    resultdb.execute(
        """
        create table if not exists "team" (
            "id"        INTEGER,
            "name"      TEXT NOT NULL UNIQUE,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
        """
    )

    # --- データ取り込みテーブル
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
        )
        """
    )

    resultdb.execute(
        """
        create table if not exists "remarks" (
            "thread_ts" TEXT NOT NULL,
            "event_ts"  TEXT NOT NULL,
            "name"      TEXT NOT NULL,
            "matter"    TEXT NOT NULL
        )
        """
    )

    resultdb.execute("drop view if exists individual_results")
    resultdb.execute(
        """
        create view if not exists individual_results as
            select
                datetime(playtime) as playtime,
                ts,
                1 as seat,
                p1_name as name,
                p1_rpoint as rpoint,
                p1_rank as rank,
                p1_point as point,
                group_concat(matter, ",") as grandslam,
                p1_name not in (select name from member) as guest,
                team.name as team,
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
            left outer join
                remarks on remarks.thread_ts = result.ts
                and remarks.name = result.p1_name
            left outer join
                member on member.name = result.p1_name
            left outer join
                team on member.team_id = team.id
            group by ts, seat, remarks.thread_ts, remarks.name
            union select
                datetime(playtime),
                ts,
                2 as seat,
                p2_name,
                p2_rpoint,
                p2_rank,
                p2_point,
                group_concat(matter, ",") as grandslam,
                p2_name not in (select name from member),
                team.name,
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
            left outer join
                remarks on remarks.thread_ts = result.ts
                and remarks.name = result.p2_name
            left outer join
                member on member.name = result.p2_name
            left outer join
                team on member.team_id = team.id
            group by ts, seat, remarks.thread_ts, remarks.name
            union select
                datetime(playtime),
                ts,
                3 as seat,
                p3_name,
                p3_rpoint,
                p3_rank,
                p3_point,
                group_concat(matter, ",") as grandslam,
                p3_name not in (select name from member),
                team.name,
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
            left outer join
                remarks on remarks.thread_ts = result.ts
                and remarks.name = result.p3_name
            left outer join
                member on member.name = result.p3_name
            left outer join
                team on member.team_id = team.id
            group by ts, seat, remarks.thread_ts, remarks.name
            union select
                datetime(playtime),
                ts,
                4 as seat,
                p4_name,
                p4_rpoint,
                p4_rank,
                p4_point,
                group_concat(matter, ",") as grandslam,
                p4_name not in (select name from member),
                team.name,
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
            left outer join
                remarks on remarks.thread_ts = result.ts
                and remarks.name = result.p4_name
            left outer join
                member on member.name = result.p4_name
            left outer join
                team on member.team_id = team.id
            group by ts, seat, remarks.thread_ts, remarks.name
        """
    )

    resultdb.execute("drop view if exists game_results")
    resultdb.execute(
        """
        create view if not exists game_results as
            select
                datetime(playtime) as playtime,
                ts,
                p1_name, p1.name isnull as p1_guest, p1_rpoint, p1_rank, p1_point,
                p2_name, p2.name isnull as p2_guest, p2_rpoint, p2_rank, p2_point,
                p3_name, p3.name isnull as p3_guest, p3_rpoint, p3_rank, p3_point,
                p4_name, p4.name isnull as p4_guest, p4_rpoint, p4_rank, p4_point,
                deposit,
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
            left outer join
                member as p1 on p1_name = p1.name
            left outer join
                member as p2 on p2_name = p2.name
            left outer join
                member as p3 on p3_name = p3.name
            left outer join
                member as p4 on p4_name = p4.name
        """
    )

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0")
    data = ret.fetchall()

    if len(data) == 0:
        g.logging.notice(f"ゲスト設定: {g.guest_name}") # type: ignore
        sql = "insert into member (id, name) values (0, ?)"
        resultdb.execute(sql, (g.guest_name,))
    elif data[0][1] != g.guest_name:
        g.logging.notice(f"ゲスト修正: {data[0][1]} -> {g.guest_name}") # type: ignore
        sql = "update member set name=? where id=0"
        resultdb.execute(sql, (g.guest_name,))

    resultdb.commit()
    resultdb.close()
