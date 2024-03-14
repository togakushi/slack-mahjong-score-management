import lib.function as f
from lib.function import global_value as g


sql_result_insert = """
    insert into
        result (
            ts, playtime,
            p1_name, p1_str, p1_rpoint, p1_rank, p1_point,
            p2_name, p2_str, p2_rpoint, p2_rank, p2_point,
            p3_name, p3_str, p3_rpoint, p3_rank, p3_point,
            p4_name, p4_str, p4_rpoint, p4_rank, p4_point,
            deposit,
            rule_version, comment
        ) values (
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?,
            ?, ?
        )
"""

sql_result_update = """
    update result set
        p1_name=?, p1_str=?, p1_rpoint=?, p1_rank=?, p1_point=?,
        p2_name=?, p2_str=?, p2_rpoint=?, p2_rank=?, p2_point=?,
        p3_name=?, p3_str=?, p3_rpoint=?, p3_rank=?, p3_point=?,
        p4_name=?, p4_str=?, p4_rpoint=?, p4_rank=?, p4_point=?,
        deposit=?
    where ts=?
"""

sql_result_delete = "delete from result where ts=?"

sql_remarks_insert = """
    insert into
        remarks (
            thread_ts, event_ts, name, matter
        ) values (
            ?, ?, ?, ?
        )
"""

sql_remarks_delete_all = "delete from remarks where thread_ts=?"

sql_remarks_delete_one = "delete from remarks where event_ts=?"


def query_count_game(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            count() as count
        from (
            select
                playtime
            from
                individual_results
            where
                rule_version = ?
                and playtime between ? and ? -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[target_player] and name in (<<target_player>>) -- 対象プレイヤー
            group by
                playtime
            order by
                playtime desc
            --[recent] limit ?
        )
    """

    placeholder = [g.rule_version, starttime, endtime]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
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


def query_get_personal_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    origin_point = g.config["mahjong"].getint("point", 250) # 配給原点
    return_point = g.config["mahjong"].getint("return", 300) # 返し点

    sql = """
        select
            name as プレイヤー,
            count() as ゲーム数,
            round(sum(point), 1) as 累積ポイント,
            round(avg(point), 1) as 平均ポイント,
            round(sum(rpoint), 1) as 累積素点,
            round(avg(rpoint), 1) as 平均素点,
            round(avg(rpoint) - ?, 1) as 平均収支1,
            round(avg(rpoint) - ?, 1) as 平均収支2,
            round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as トップ率,
            round(cast(count(rank <= 2 or null) as real) / count() * 100, 2) as 連対率,
            round(cast(count(rank <= 3 or null) as real) / count() * 100, 2) as ラス回避率,
            count(rank = 1 or null) as '1位',
            count(rank = 2 or null) as '2位',
            count(rank = 3 or null) as '3位',
            count(rank = 4 or null) as '4位',
            round(avg(rank), 2) as 平均順位,
            count(rpoint < 0 or null) as トビ回数,
            round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as トビ率,
            ifnull(sum(gs_count), 0) as 役満和了,
            round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100,2 ) as 役満和了率,
            min(playtime) as first_game,
            max(playtime) as last_game
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
            order by
                playtime desc
            --[recent] limit ? * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= ? -- 規定打数
        order by
            count() desc
    """

    placeholder = [origin_point, return_point, g.guest_name, g.rule_version, starttime, endtime, command_option["stipulated"]]

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
        placeholder += [target_count]

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
