import lib.function as f
from lib.function import global_value as g


def for_report_personal_data(argument, command_option, flag = "M"):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            <<collection>>,
            count() as ゲーム数,
            round(sum(point), 1) as 累積ポイント,
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
            rule_version = ?
            and playtime between ? and ?
            and name = ?
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



    placeholder = [g.rule_version, starttime, endtime, target_player[0]]

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {placeholder}") # type: ignore

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def for_report_count_data(argument, command_option, interval = 40):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            min(game_count) as 開始,
            max(game_count) as 終了,
            count() as ゲーム数,
            round(sum(point), 1) as 累積ポイント,
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
                (row_number() over (order by game_count desc) - 1) / ? as interval,
                game_count, rank, point, rpoint
            from (
                select
                    row_number() over (order by playtime) as game_count,
                    rank, point, rpoint
                from
                    individual_results
                where
                    rule_version = ?
                    and name = ?
            )
            order by
                game_count desc
        )
        group by interval
    """

    placeholder = [interval, g.rule_version, target_player[0]]

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {placeholder}") # type: ignore

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def for_report_count_moving(argument, command_option, interval = 40):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

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
                    rule_version = ?
                    and name = ?
            )
            order by
                total_count desc
        )
        window
            moving as (partition by interval order by total_count)
        order by
            total_count
    """

    if interval == 0:
        sql = sql.replace("<<Calculation Formula>>", "?")
    else:
        sql = sql.replace(
            "<<Calculation Formula>>",
            "(row_number() over (order by total_count desc) - 1) / ?"
        )

    placeholder = [interval, g.rule_version, target_player[0]]

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {placeholder}") # type: ignore

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }
