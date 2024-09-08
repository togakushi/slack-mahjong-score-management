import logging

import global_value as g


def for_report_personal_data(flag="M"):
    sql = """
        select
            <<collection>>,
            count() as ゲーム数,
            round(sum(point), 1) as 通算ポイント,
            round(avg(point), 1) as 平均ポイント,
            count(rank = 1 or NULL) as "1位",
            round(cast(count(rank = 1 or NULL) AS real) / cast(count() as real) * 100, 2) as "1位率",
            count(rank = 2 or NULL) as "2位",
            round(cast(count(rank = 2 or NULL) AS real) / cast(count() as real) * 100, 2) as "2位率",
            count(rank = 3 or NULL) as "3位",
            round(cast(count(rank = 3 or NULL) AS real) / cast(count() as real) * 100, 2) as "3位率",
            count(rank = 4 or NULL) as "4位",
            round(cast(count(rank = 4 or NULL) AS real) / cast(count() as real) * 100, 2) as "4位率",
            round(avg(rank), 2) AS 平均順位,
            count(rpoint < -1 or NULL) as トビ,
            round(cast(count(rpoint < -1 OR NULL) AS real) / cast(count() as real) * 100, 2) as トビ率
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            and name = :player_name
        <<group by>>
        order by
            collection desc
    """

    match flag:
        case "M":
            sql = sql.replace("<<collection>>", "collection as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    logging.trace(f"sql: {sql}")  # type: ignore
    logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def for_report_count_data(interval=40):
    sql = """
        select
            min(game_count) as 開始,
            max(game_count) as 終了,
            count() as ゲーム数,
            round(sum(point), 1) as 通算ポイント,
            round(avg(point), 1) as 平均ポイント,
            count(rank = 1 or NULL) as "1位",
            round(cast(count(rank = 1 or NULL) AS real) / cast(count() as real) * 100, 2) as "1位率",
            count(rank = 2 or NULL) as "2位",
            round(cast(count(rank = 2 or NULL) AS real) / cast(count() as real) * 100, 2) as "2位率",
            count(rank = 3 or NULL) as "3位",
            round(cast(count(rank = 3 or NULL) AS real) / cast(count() as real) * 100, 2) as "3位率",
            count(rank = 4 or NULL) as "4位",
            round(cast(count(rank = 4 or NULL) AS real) / cast(count() as real) * 100, 2) as "4位率",
            round(avg(rank), 2) AS 平均順位,
            count(rpoint < -1 or NULL) as トビ,
            round(cast(count(rpoint < -1 OR NULL) AS real) / cast(count() as real) * 100, 2) as トビ率
        from (
            select
                (row_number() over (order by game_count desc) - 1) / :interval as interval,
                game_count, rank, point, rpoint
            from (
                select
                    row_number() over (order by playtime) as game_count,
                    rank, point, rpoint
                from
                    individual_results
                where
                    rule_version = :rule_version
                    and name = :player_name
            )
            order by
                game_count desc
        )
        group by interval
    """

    g.prm.append({"interval": interval})

    logging.trace(f"sql: {sql}")  # type: ignore
    logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def for_report_count_moving(interval=40):
    sql = """
        select
            interval,
            row_number() over (partition by interval) as game_no,
            total_count,
            playtime,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(rank) over moving, 2) as rank_avg
        from (
            select
                <<Calculation Formula>> as interval,
                total_count, playtime, rank, point
            from (
                select
                    row_number() over (order by playtime) as total_count,
                    playtime, rank, point
                from
                    individual_results
                where
                    rule_version = :rule_version
                    and name = :player_name
            )
            order by
                total_count desc
        )
        window
            moving as (partition by interval order by total_count)
        order by
            total_count
    """

    g.prm.append({"interval": interval})

    if interval == 0:
        sql = sql.replace("<<Calculation Formula>>", ":interval")
    else:
        sql = sql.replace(
            "<<Calculation Formula>>",
            "(row_number() over (order by total_count desc) - 1) / :interval"
        )

    logging.trace(f"sql: {sql}")  # type: ignore
    logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore
    return (sql)
