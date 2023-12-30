import lib.function as f
from lib.function import global_value as g

def query_count_game(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        --[recent] select * from (
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
        --[recent] )
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
