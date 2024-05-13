import lib.database as d
from lib.function import global_value as g


def game_count(argument, command_option):
    """
    ゲーム数をカウントするSQLを返す
    """

    params = d.common.placeholder_params(argument, command_option)
    sql = """
        select
            count() as count,
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                playtime
            from
                individual_results
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
            group by
                playtime
            order by
                playtime desc
            --[recent] limit :target_count
        )
    """

    if params["player_name"]:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace("<<player_list>>", ":" + ", :".join([x for x in params["player_list"].keys()]))

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")

    if params["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    return(sql)


def record_count():
    """
    連測連対などの記録をカウントするSQLを生成
    """

    sql = """
        select
            playtime,
            name as "プレイヤー名",
            rank as "順位",
            point as "獲得ポイント",
            rpoint as "最終素点"
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
        """

    return(sql)


def personal_results(argument, command_option):
    """
    個人成績を集計するSQLを生成
    """

    params = d.common.placeholder_params(argument, command_option)
    sql = """
        select
            name as プレイヤー名,
            count() as ゲーム数,
            count(rank = 1 or null) as '1st',
            count(rank = 2 or null) as '2nd',
            count(rank = 3 or null) as '3rd',
            count(rank = 4 or null) as '4th',
            round(sum(point), 1) as 累積ポイント,
            round(avg(point), 1) as 平均ポイント,
            round(avg(rank), 2) as 平均順位,
            count(rpoint < 0 or null) as トビ,
            ifnull(sum(gs_count), 0) as 役満和了,
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
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                rpoint,
                rank,
                point,
                seat,
                matter,
                gs_count
            from
                individual_results
            left outer join
                (select thread_ts, name, count() as gs_count, matter from remarks group by thread_ts, name) as remarks
                on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and individual_results.name in (<<player_list>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            sum(point) desc
    """

    if params["player_name"]:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace("<<player_list>>", ":" + ", :".join([x for x in params["player_list"].keys()]))

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")

    if params["target_count"] != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")

    g.logging.trace(f"sql: {sql}") # type: ignore
    return(sql)
