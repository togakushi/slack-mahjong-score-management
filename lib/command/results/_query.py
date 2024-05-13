import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def select_personal_data(argument, command_option, cur):
    """
    個人成績を返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    cur : object
        カーソル

    Returns
    -------
    data : dict
        集計結果
    """

    prams = d.common.placeholder_params(argument, command_option)
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
            where individual_results.name = :player_name
            order by playtime desc
            --[recent] limit :target_count
        ) individual_results
        left outer join
            remarks on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
        group by
            individual_results.name
    """

    if prams["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {prams}") # type: ignore

    rows = cur.execute(sql, prams)
    data = rows.fetchone()

    if not data:
        data = {
            "name": prams["player_name"],
            "game": 0, "win": 0, "lose": 0, "draw": 0,
        }

    return(data)


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
                --<<select player>>--
            order by
                playtime desc
            --[recent] limit ?
        )
        order by
            playtime
        """

    placeholder = [g.rule_version, starttime, endtime]

    s = ""
    for i in target_player:
        s += "and ? in (p1_name, p2_name, p3_name, p4_name)\n"
        placeholder.append(i)
    sql = sql.replace("--<<select player>>--", s)

    if target_count != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, target_player[0], target_count]

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


def select_game_vs_results(argument, command_option, my_name, vs_name):
    target_days, _, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target: {my_name} vs {vs_name}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select * from (
            select
                replace(playtime, "-", "/") as playtime,
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
                and ? in (p1_name, p2_name, p3_name, p4_name)
            order by
                playtime desc
            --[recent] limit ?
        )
        order by
            playtime
        """

    placeholder = [g.rule_version, starttime, endtime, my_name, vs_name]

    if target_count != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, my_name, vs_name, target_count]

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {placeholder}") # type: ignore

    return {
        "target_days": target_days,
        "target_player": [my_name, vs_name],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_versus_matrix(argument, command_option, cur):
    """
    直接対戦結果を返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    cur : object
        カーソル

    Returns
    -------
    results : dict
        集計結果

    prams : dict
        検索条件
    """

    prams = d.common.placeholder_params(argument, command_option)
    sql = """
        select
            my_name, vs_name,
            count() as game,
            count(my_rank < vs_rank or null) as win,
            count(my_rank > vs_rank or null) as lose,
            round(cast(count(my_rank < vs_rank or null) AS real) / count() * 100, 2) as 'win%',
            round(sum(my_point),1 ) as my_point_sum,
            round(avg(my_point),1 ) as my_point_avg,
            round(sum(vs_point), 1) as vs_point_sum,
            round(avg(vs_point), 1) as vs_point_avg,
            round(avg(my_rpoint), 1) as my_rpoint_avg,
            round(avg(vs_rpoint), 1) as vs_rpoint_avg,
            count(my_rank = 1 or null) as my_1st,
            count(my_rank = 2 or null) as my_2nd,
            count(my_rank = 3 or null) as my_3rd,
            count(my_rank = 4 or null) as my_4th,
            round(avg(my_rank), 2) as my_rank_avg,
            count(vs_rank = 1 or null) as vs_1st,
            count(vs_rank = 2 or null) as vs_2nd,
            count(vs_rank = 3 or null) as vs_3rd,
            count(vs_rank = 4 or null) as vs_4th,
            round(avg(vs_rank), 2) as vs_rank_avg
        from (
            select
                my.name as my_name,
                my.rank as my_rank,
                my.rpoint as my_rpoint,
                my.point as my_point,
                --[unregistered_replace] case when vs.guest = 0 then vs.name else :guest_name end as vs_name, -- ゲスト有効
                --[unregistered_not_replace] vs.name as vs_name, -- ゲスト無効
                vs.rank as vs_rank,
                vs.rpoint as vs_rpoint,
                vs.point as vs_point
            from
                individual_results my
            inner join
                individual_results vs
                    on (my.playtime = vs.playtime and my.name != vs.name)
            where
                my.rule_version = :rule_version
                and my.playtime between :starttime and :endtime
                and my.name = :player_name
                --[guest_not_skip] and vs.playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and vs.guest = 0 -- ゲストなし
            order by
                my.playtime desc
            --[recent] limit :target_count
        )
        group by
            my_name, vs_name
        order by
            game desc
    """

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")

    if prams["target_count"] != 0:
        sql = sql.replace("and my.playtime between", "-- and my.playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {prams}") # type: ignore

    rows = cur.execute(sql, prams)

    results = {}
    for row in rows.fetchall():
        results[row["vs_name"]] = dict(row)
        g.logging.trace(f"{row['vs_name']}: {results[row['vs_name']]}") # type: ignore

    return(results, prams)


def select_game(argument, command_option, cur):
    """
    ゲーム結果を返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    cur : object
        カーソル

    Returns
    -------
    results : dict
        集計結果

    name_list : list
        集計対象メンバーリスト(ゲストフラグ付き)

    params : dict
        検索条件
    """

    params = d.common.placeholder_params(argument, command_option)
    sql = """
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
            max(playtime) as last_game,
            max(ts) as max_ts
        from (
            select
                playtime, ts,
                --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                rpoint, rank, point, guest, rule_version
            from
                individual_results
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit :target_count
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            pt_total desc
    """

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
    if params["player_name"]:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace("<<player_list>>", ":" + ", :".join([x for x in params["player_list"].keys()]))
    if params["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    g.logging.trace(f"placeholder: {params}") # type: ignore

    rows = cur.execute(sql, params)

    # ---
    results = {}
    name_list = []
    for row in rows.fetchall():
        results[row["name"]] = dict(row)
        name_list.append(c.member.NameReplace(row["name"], command_option, add_mark = True))

    return(results, name_list, params)
