import logging
import sqlite3

import lib.global_value as g


def initialization_resultdb():
    """DB初期化処理
    """

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
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

    resultdb.execute(
        """
        create table if not exists "words" (
            "word"     TEXT NOT NULL UNIQUE,
            "type"     INTEGER,
            "ex_point" INTEGER
        )
        """
    )

    # wordsテーブル情報読み込み(regulations)
    if g.cfg.config.has_section("regulations"):
        resultdb.execute("delete from words")
        for k, v in g.cfg.config.items("regulations"):
            match k:
                case "undefined":
                    if v in ("0", "2"):
                        g.undefined_word = int(v)
                case "type0" | "yakuman":
                    words_list = set([x.strip() for x in v.split(",")])
                    for word in words_list:
                        resultdb.execute(
                            "insert into words(word, type, ex_point) values (?, 0, NULL)",
                            (word,)
                        )
                    logging.info("regulations table(type0): %s", words_list)
                case "type2":
                    words_list = set([x.strip() for x in v.split(",")])
                    for word in words_list:
                        resultdb.execute(
                            "insert into words(word, type, ex_point) values (?, 2, NULL)",
                            (word,)
                        )
                    logging.info("regulations table(type2): %s", words_list)
                case _:
                    word = k.strip()
                    ex_point = int(v)
                    resultdb.execute(
                        "insert into words(word, type, ex_point) values (?, 1, ?)",
                        (word, ex_point,)
                    )
                    logging.info("regulations table(type1): %s, %s", word, ex_point)

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
                p1_point + ifnull(ex_point, 0) as point,
                grandslam,
                ifnull(ex_point, 0) as ex_point,
                p1_name not in (select name from member) as guest,
                date(result.playtime, '-12 hours') as collection_daily,
                rule_version,
                comment
            from
                result
            left join
                member on member.name = result.p1_name
            left join
                grandslam on grandslam.thread_ts == result.ts
                and grandslam.name = result.p1_name
            left join
                regulations on regulations.thread_ts == result.ts
                and regulations.name == result.p1_name
            group by ts, seat
            union select
                datetime(playtime),
                ts,
                2 as seat,
                p2_name,
                p2_rpoint,
                p2_rank,
                p2_point + ifnull(ex_point, 0),
                grandslam,
                ifnull(ex_point, 0),
                p2_name not in (select name from member),
                date(result.playtime, '-12 hours'),
                rule_version,
                comment
            from
                result
            left join
                member on member.name = result.p2_name
            left join
                grandslam on grandslam.thread_ts == result.ts
                and grandslam.name = result.p2_name
            left join
                regulations on regulations.thread_ts == result.ts
                and regulations.name == result.p2_name
            group by ts, seat
            union select
                datetime(playtime),
                ts,
                3 as seat,
                p3_name,
                p3_rpoint,
                p3_rank,
                p3_point + ifnull(ex_point, 0),
                grandslam,
                ifnull(ex_point, 0),
                p3_name not in (select name from member),
                date(result.playtime, '-12 hours'),
                rule_version,
                comment
            from
                result
            left join
                member on member.name = result.p3_name
            left join
                grandslam on grandslam.thread_ts == result.ts
                and grandslam.name = result.p3_name
            left join
                regulations on regulations.thread_ts == result.ts
                and regulations.name == result.p3_name
            group by ts, seat
            union select
                datetime(playtime),
                ts,
                4 as seat,
                p4_name,
                p4_rpoint,
                p4_rank,
                p4_point + ifnull(ex_point, 0),
                grandslam,
                ifnull(ex_point, 0),
                p4_name not in (select name from member),
                date(result.playtime, '-12 hours'),
                rule_version,
                comment
            from
                result
            left join
                member on member.name = result.p4_name
            left join
                grandslam on grandslam.thread_ts == result.ts
                and grandslam.name = result.p4_name
            left join
                regulations on regulations.thread_ts == result.ts
                and regulations.name == result.p4_name
            group by ts, seat
        """
    )

    resultdb.execute("drop view if exists team_results")
    resultdb.execute(
        """
        create view if not exists team_results as
            select
                datetime(result.playtime) as playtime,
                result.ts,
                1 as seat,
                ifnull(team.name, "未所属") as name,
                result.p1_rpoint as rpoint,
                result.p1_rank as rank,
                round(result.p1_point, 1) + ifnull(regulations.ex_point, 0) as point,
                regulations.ex_point,
                date(result.playtime, '-12 hours') as collection_daily,
                result.rule_version,
                result.comment
            from
                result
            join member on
                result.p1_name = member.name
            left join team on
                member.team_id = team.id
            left join regulations on
                regulations.thread_ts == result.ts
                and regulations.name == result.p1_name
            union select
                datetime(result.playtime) as playtime,
                result.ts,
                2 as seat,
                ifnull(team.name, "未所属") as name,
                result.p2_rpoint as rpoint,
                result.p2_rank as rank,
                round(result.p2_point, 1) + ifnull(regulations.ex_point, 0) as point,
                regulations.ex_point,
                date(result.playtime, '-12 hours') as collection_daily,
                result.rule_version,
                result.comment
            from
                result
            join member on
                result.p2_name = member.name
            left join team on
                member.team_id = team.id
            left join regulations on
                regulations.thread_ts == result.ts
                and regulations.name == result.p2_name
            union select
                datetime(result.playtime) as playtime,
                result.ts,
                3 as seat,
                ifnull(team.name, "未所属") as name,
                result.p3_rpoint as rpoint,
                result.p3_rank as rank,
                round(result.p3_point, 1) + ifnull(regulations.ex_point, 0) as point,
                regulations.ex_point,
                date(result.playtime, '-12 hours') as collection_daily,
                result.rule_version,
                result.comment
            from
                result
            join member on
                result.p3_name = member.name
            left join team on
                member.team_id = team.id
            left join regulations on
                regulations.thread_ts == result.ts
                and regulations.name == result.p3_name
            union select
                datetime(result.playtime) as playtime,
                result.ts,
                4 as seat,
                ifnull(team.name, "未所属") as name,
                result.p4_rpoint as rpoint,
                result.p4_rank as rank,
                round(result.p4_point, 1) + ifnull(regulations.ex_point, 0) as point,
                regulations.ex_point,
                date(result.playtime, '-12 hours') as collection_daily,
                result.rule_version,
                result.comment
            from
                result
            join member on
                result.p4_name = member.name
            left join team on
                member.team_id = team.id
            left join regulations on
                regulations.thread_ts == result.ts
                and regulations.name == result.p4_name
        """
    )

    resultdb.execute("drop view if exists game_results")
    resultdb.execute(
        """
        create view if not exists game_results as
            select
                datetime(result.playtime) as playtime, result.ts,
                p1_name, p1_team.name as p1_team,
                p1.name isnull as p1_guest, p1_rpoint, p1_rank, p1_point,
                p2_name, p2_team.name as p2_team,
                p2.name isnull as p2_guest, p2_rpoint, p2_rank, p2_point,
                p3_name, p3_team.name as p3_team,
                p3.name isnull as p3_guest, p3_rpoint, p3_rank, p3_point,
                p4_name, p4_team.name as p4_team,
                p4.name isnull as p4_guest, p4_rpoint, p4_rank, p4_point,
                deposit,
                date(result.playtime, '-12 hours') as collection_daily,
                result.comment,
                game_info.guest_count,
                game_info.same_team,
                result.rule_version
            from
                result
            join game_info on game_info.ts = result.ts
            left join member as p1 on p1.name = result.p1_name
            left join member as p2 on p2.name = result.p2_name
            left join member as p3 on p3.name = result.p3_name
            left join member as p4 on p4.name = result.p4_name
            left join team as p1_team on p1.team_id = p1_team.id
            left join team as p2_team on p2.team_id = p2_team.id
            left join team as p3_team on p3.team_id = p3_team.id
            left join team as p4_team on p4.team_id = p4_team.id
        """
    )

    resultdb.execute("drop view if exists game_info")
    resultdb.execute(
        """
        create view if not exists game_info as
            select
                datetime(playtime) as playtime,
                ts,
                case when p1.id isnull then 1 else 0 END +
                case when p2.id isnull then 1 else 0 END +
                case when p3.id isnull then 1 else 0 END +
                case when p4.id isnull then 1 else 0 END as guest_count,
                case
                    when p1.team_id = p2.team_id then 1
                    when p1.team_id = p3.team_id then 1
                    when p1.team_id = p4.team_id then 1
                    when p2.team_id = p3.team_id then 1
                    when p2.team_id = p4.team_id then 1
                    when p3.team_id = p4.team_id then 1
                    else 0
                end as same_team,
                comment,
                rule_version
            from
                result
            left join member as p1
                on p1_name = p1.name
            left join member as p2
                on p2_name = p2.name
            left join member as p3
                on p3_name = p3.name
            left join member as p4
                on p4_name = p4.name
        """
    )

    # メモ
    if g.undefined_word == 0:
        grandslam_where = "words.type is null or words.type == 0"
        regulation_where = "words.type in (1, 2)"
    elif g.undefined_word == 2:
        grandslam_where = "words.type == 0"
        regulation_where = "words.type is null or words.type in (1, 2)"
    else:
        grandslam_where = "words.type == 0"
        regulation_where = "words.type in (1, 2)"

    resultdb.execute("drop view if exists grandslam")
    resultdb.execute(
        f"""
        create view if not exists grandslam as
            select
                remarks.thread_ts,
                remarks.name,
                team.name as team,
                group_concat(remarks.matter) as grandslam,
                count() as gs_count,
                game_info.guest_count,
                game_info.same_team
            from
                remarks
            left join member on
                member.name == remarks.name
            left join team on
                member.team_id == team.id
            left join words on
                words.word == remarks.matter
            join game_info on
                game_info.ts == remarks.thread_ts
            where
                {grandslam_where}
            group by
                remarks.thread_ts, remarks.name
        """
    )

    resultdb.execute("drop view if exists regulations")
    resultdb.execute(
        f"""
        create view if not exists regulations as
            select
                remarks.thread_ts,
                remarks.name as name,
                team.name as team,
                group_concat(remarks.matter) as word,
                sum(words.ex_point) as ex_point,
                ifnull(words.type, 0) as type,
                game_info.guest_count,
                game_info.same_team
            from
                remarks
            left join member on
                member.name == remarks.name
            left join team on
                member.team_id == team.id
            left join words on
                words.word == remarks.matter
            join game_info on
                game_info.ts == remarks.thread_ts
            where
                {regulation_where}
            group by
                remarks.thread_ts, remarks.name
        """
    )

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0")
    data = ret.fetchall()

    if len(data) == 0:
        logging.notice("ゲスト設定: %s", g.prm.guest_name)
        sql = "insert into member (id, name) values (0, ?)"
        resultdb.execute(sql, (g.prm.guest_name,))
    elif data[0][1] != g.prm.guest_name:
        logging.notice("ゲスト修正: %s -> %s", data[0][1], g.prm.guest_name)
        sql = "update member set name=? where id=0"
        resultdb.execute(sql, (g.prm.guest_name,))

    resultdb.commit()
    resultdb.close()
