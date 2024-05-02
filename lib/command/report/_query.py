import lib.function as f
from lib.function import global_value as g


def select_personal_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            name as プレイヤー,
            count() as ゲーム数,
            replace(round(sum(point), 1), "-", "▲") as 累積ポイント,
            replace(round(avg(point), 1), "-", "▲") as 平均ポイント,
            printf("%3d (%7.2f%%)",
                count(rank = 1 or null),
                round(cast(count(rank = 1 or null) as real) / count() * 100, 2)
            ) as '1位',
            printf("%3d (%7.2f%%)",
                count(rank = 2 or null),
                round(cast(count(rank = 2 or null) as real) / count() * 100, 2)
            ) as '2位',
            printf("%3d (%7.2f%%)",
                count(rank = 3 or null),
                round(cast(count(rank = 3 or null) as real) / count() * 100, 2)
            ) as '3位',
            printf("%3d (%7.2f%%)",
                count(rank = 4 or null),
                round(cast(count(rank = 4 or null) AS real) / count() * 100, 2)
            ) as '4位',
            printf("%.2f", round(avg(rank), 2)) as 平均順位,
            printf("%3d (%7.2f%%)",
                count(rpoint < 0 or null),
                round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2)
            ) as トビ,
            printf("%3d (%7.2f%%)",
                ifnull(sum(gs_count), 0),
                round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2)
            ) as 役満和了,
            min(playtime) as first_game,
            max(playtime) as last_game,
            sum(point) as 並び変え用カラム
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then individual_results.name else ? end as name, -- ゲスト有効
                --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                rpoint,
                rank,
                point,
                gs_count
            from
                individual_results
            left outer join
                (select thread_ts, name,count() as gs_count from remarks group by thread_ts, name) as remarks
                on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
            where
                rule_version = ?
                and playtime between ? and ?
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[target_player] and individual_results.name in (<<target_player>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit ? * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= ? -- 規定打数
        order by
            並び変え用カラム desc
    """

    placeholder = [g.guest_name, g.rule_version, starttime, endtime]

    if target_player:
        sql = sql.replace("--[target_player] ", "")
        p = []
        for i in target_player:
            p.append("?")
            placeholder.append(i)
        sql = sql.replace("<<target_player>>", ",".join([i for i in p]))

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))

    if target_count != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder.pop(placeholder.index(starttime))
        placeholder.pop(placeholder.index(endtime))
        placeholder.insert(1, target_count)

    placeholder.append(command_option["stipulated"])

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
