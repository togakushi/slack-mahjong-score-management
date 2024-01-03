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
            individual_results.name,
            count() as game,
            count(point > 0 or null) as win, count(point < 0 or null) as lose, count(point = 0 or null) as draw,
            round(sum(point), 1) as pt_total, round(avg(point), 1) as pt_avg,
            count(rank = 1 or null) as '1st', round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as '1st%',
            count(rank = 2 or null) as '2nd', round(cast(count(rank = 2 or null) as real) / count() * 100, 2) as '2nd%',
            count(rank = 3 or null) as '3rd', round(cast(count(rank = 3 or null) as real) / count() * 100, 2) as '3rd%',
            count(rank = 4 or null) as '4th', round(cast(count(rank = 4 or null) AS real) / count() * 100, 2) as '4th%',
            round(avg(rank), 2) as rank_avg,
            count(matter) as gs, round(cast(count(matter) as REAL) / count() * 100, 2) as 'gs%',
            count(rpoint < 0 or null) as flying, round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as 'flying%',
            -- 座席順位分布
            count(seat = 1 and rank = 1 or null) as 's1-1st',
            count(seat = 1 and rank = 2 or null) as 's1-2nd',
            count(seat = 1 and rank = 3 or null) as 's1-3rd',
            count(seat = 1 and rank = 4 or null) as 's1-4th',
            round(avg(case when seat = 1 then rank end), 2) as 's1-rank_avg',
            count(seat = 1 and matter != '' or null) as 's1-gs',
            count(seat = 1 and rpoint < 0 or null) as 's1-flying',
            count(seat = 2 and rank = 1 or null) as 's2-1st',
            count(seat = 2 and rank = 2 or null) as 's2-2nd',
            count(seat = 2 and rank = 3 or null) as 's2-3rd',
            count(seat = 2 and rank = 4 or null) as 's2-4th',
            round(avg(case when seat = 2 then rank end), 2) as 's2-rank_avg',
            count(seat = 2 and matter != '' or null) as 's2-gs',
            count(seat = 2 and rpoint < 0 or null) as 's2-flying',
            count(seat = 3 and rank = 1 or null) as 's3-1st',
            count(seat = 3 and rank = 2 or null) as 's3-2nd',
            count(seat = 3 and rank = 3 or null) as 's3-3rd',
            count(seat = 3 and rank = 4 or null) as 's3-4th',
            round(avg(case when seat = 3 then rank end), 2) as 's3-rank_avg',
            count(seat = 3 and matter != '' or null) as 's3-gs',
            count(seat = 3 and rpoint < 0 or null) as 's3-flying',
            count(seat = 4 and rank = 1 or null) as 's4-1st',
            count(seat = 4 and rank = 2 or null) as 's4-2nd',
            count(seat = 4 and rank = 3 or null) as 's4-3rd',
            count(seat = 4 and rank = 4 or null) as 's4-4th',
            round(avg(case when seat = 4 then rank end), 2) as 's4-rank_avg',
            count(seat = 4 and matter != '' or null) as 's4-gs',
            count(seat = 4 and rpoint < 0 or null) as 's4-flying',
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select * from individual_results
            where individual_results.name = ?
            order by playtime desc
            --[recent] limit ?
        ) individual_results
        left outer join
            remarks on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
        where
            rule_version = ?
            and playtime between ? and ?
        group by
            individual_results.name
    """

    if target_count == 0:
        placeholder = [target_player[0], g.rule_version, starttime, endtime]
    else:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [target_player[0], target_count, g.rule_version]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_game_results(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select * from (
            select
                playtime, ts,
                p1_guest + p2_guest + p3_guest + p4_guest as guest_count,
                p1_name, p1_rpoint * 100 as p1_rpoint, p1_rank, p1_point,
                p2_name, p2_rpoint * 100 as p2_rpoint, p2_rank, p2_point,
                p3_name, p3_rpoint * 100 as p3_rpoint, p3_rank, p3_point,
                p4_name, p4_rpoint * 100 as p4_rpoint, p4_rank, p4_point
            from
                game_results
            where
                rule_version = ?
                and playtime between ? and ?
                and ? in (p1_name, p2_name, p3_name, p4_name)
            order by
                playtime desc
            --[recent] limit ?
        )
        order by
            playtime
        """

    if target_count == 0:
        placeholder = [g.rule_version, starttime, endtime, target_player[0]]
    else:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, target_player[0], target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_versus_matrix(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            my_name, vs_name,
            count() as game,
            count(my_rank < vs_rank or null) as win,
            count(my_rank > vs_rank or null) as lose,
            round(cast(count(my_rank < vs_rank or null) AS real) / count() * 100, 2) as 'win%'
        from (
            select
                my.name as my_name,
                my.rank as my_rank,
                vs.name as vs_name,
                vs.rank as vs_rank
            from
                individual_results my
            inner join
                individual_results vs
                    on (my.playtime = vs.playtime and my.name != vs.name)
            where
                my.rule_version = ?
                and my.playtime between ? and ?
                and my.name = ?
            order by
                my.playtime desc
            --[recent] limit ?
        )
        group by
            my_name, vs_name
        order by
            game desc
    """

    if target_count == 0:
        placeholder = [g.rule_version, starttime, endtime, target_player[0]]
    else:
        sql = sql.replace("and my.playtime between", "-- and my.playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, target_player[0], target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_game(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        --[recent] select * from (
        select
            name,
            count() as count,
            round(sum(point), 1) as pt_total,
            round(avg(point), 1) as pt_avg,
            count(rank = 1 or null) as "1st",
            count(rank = 2 or null) as "2nd",
            count(rank = 3 or null) as "3rd",
            count(rank = 4 or null) as "4th",
            round(avg(rank), 2) as rank_avg,
            count(rpoint < 0 or null) as flying,
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then name else ? end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                rpoint, rank, point, guest, rule_version
            from
                individual_results
            where
                rule_version = ?
                and playtime between ? and ? -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[guest_skip] and guest = 0 -- ゲストなし
                --[target_player] and name in (<<target_player>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit ?
        )
        group by
            name
        order by
            pt_total desc
        --[recent] )
    """

    placeholder = [g.guest_name, g.rule_version, starttime, endtime]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))
    if target_player:
        sql = sql.replace("--[target_player] ", "")
        p = []
        for i in target_player:
            p.append("?")
            placeholder.append(i)
        sql = sql.replace("<<target_player>>", ",".join([i for i in p]))

    if target_count != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder.pop(placeholder.index(starttime))
        placeholder.pop(placeholder.index(endtime))
        placeholder += [target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }
