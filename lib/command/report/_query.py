import lib.function as f
from lib.function import global_value as g


def select_game_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            collection as 集計月,
            count() / 4 as ゲーム数,
            replace(printf("%.1f pt", round(sum(point) , 1)), "-", "▲") as 供託,
            count(rpoint < -1 or null) as "飛んだ人数(延べ)",
            printf("%.2f%",	round(cast(count(rpoint < -1 or null) as real) / cast(count() / 4 as real) * 100, 2)) as トビ終了率,
            replace(printf("%s", max(rpoint)), "-", "▲") as 最大素点,
            replace(printf("%s", min(rpoint)), "-", "▲") as 最小素点
        from
            individual_results
        where
            rule_version = ?
            and playtime between ? and ?
        group by
            collection
        order by
            collection desc
    """

    placeholder = [g.rule_version, starttime, endtime]

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


def select_winner(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            collection as "集計月",
            replace(printf("%s (%.1fpt)",
                max(case when rank = 1 then name end),
                max(case when rank = 1 then total end)
            ), "-", "▲") as "1位",
            replace(printf("%s (%.1fpt)",
                max(case when rank = 2 then name end),
                max(case when rank = 2 then total end)
            ), "-", "▲") as "2位",
            replace(printf("%s (%.1fpt)",
                max(case when rank = 3 then name end),
                max(case when rank = 3 then total end)
            ), "-", "▲") as "3位",
            replace(printf("%s (%.1fpt)",
                max(case when rank = 4 then name end),
                max(case when rank = 4 then total end)
            ), "-", "▲") as "4位",
            replace(printf("%s (%.1fpt)",
                max(case when rank = 5 then name end),
                max(case when rank = 5 then total end)
            ), "-", "▲") as "5位"
        from (
            select
                collection,
                rank() over (partition by collection order by round(sum(point), 1) desc) as rank,
                name,
                round(sum(point), 1) as total
            from (
                select
                    collection,
                    --[unregistered_replace] case when guest = 0 then name else ? end as name, -- ゲスト有効
                    --[unregistered_not_replace] name, -- ゲスト無効
                    point
                from
                    individual_results
                where
                    rule_version = ?
                    and playtime between ? and ?
                    --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                    --[guest_skip] and guest = 0 -- ゲストなし
            )
            group by
                name, collection
            having
                count() >= ? -- 規定打数
        )
        group by
            collection
        order by
            collection desc
    """

    placeholder = [g.guest_name, g.rule_version, starttime, endtime, command_option["stipulated"]]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))

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
