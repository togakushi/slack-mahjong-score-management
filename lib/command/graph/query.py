import lib.function as f
from lib.function import global_value as g


def select_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            count() over moving as count,
            replace(playtime, "-", "/") as playtime,
            name,
            rank,
            point,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(point) over moving, 1) as point_avg,
            round(avg(rank) over moving, 2) as rank_avg
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then name else ? end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                rank,
                point
            from
                individual_results
            where
                rule_version = ?
                and playtime between ? and ?
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[target_player] and name in (<<target_player>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit ?
        )
        window
            moving as (partition by name order by playtime)
        order by
            name, playtime
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
        if command_option["fourfold"]:
            placeholder.append(target_count * 4)
        else:
            placeholder.append(target_count)

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
