
import global_value as g
from lib.database.common import query_modification


def record_count():
    """連続連対などの記録をカウントするSQLを生成

    Returns:
        str: SQL
    """

    sql = """
        -- ranking.record_count()
        select
            individual_results.playtime,
            --[individual] --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
            --[individual] --[unregistered_not_replace] individual_results.name, -- ゲスト無効
            --[team] individual_results.name,
            rank as "順位",
            point as "獲得ポイント",
            rpoint as "最終素点"
        from
            individual_results
        join game_info on
            game_info.ts == individual_results.ts
        where
            individual_results.rule_version = :rule_version
            and individual_results.playtime between :starttime and :endtime
            --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
            --[individual] --[guest_skip] and guest = 0 -- ゲストなし
            --[friendly_fire] and same_team = 0
            --[team] and individual_results.name notnull
            --[player_name] and individual_results.name in (<<player_list>>) -- 対象プレイヤー
            --[search_word] and game_info.comment like :search_word
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))


def ratings():
    """レーティング集計用

    Returns:
        str: SQL
    """

    sql = """
        -- ranking.ratings()
        select
            playtime,
            p1_name, p1_rank,
            p2_name, p2_rank,
            p3_name, p3_rank,
            p4_name, p4_rank
        from
            game_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
    """

    return (query_modification(sql))


def results():
    """成績集計(シンプル版)

    Returns:
        str: SQL
    """

    sql = """
        -- ranking.results()
        select
            individual_results.name,
            count() as count,
            printf("%d+%d+%d+%d=%d",
                count(rank = 1 or null),
                count(rank = 2 or null),
                count(rank = 3 or null),
                count(rank = 4 or null),
                count()
            ) as rank_dist,
            round(avg(rpoint) * 100, 1) as rpoint_avg,
            round(avg(rank), 2) as rank_avg
        from
            individual_results
        join game_info on
            game_info.ts == individual_results.ts
        where
            individual_results.rule_version = :rule_version
            and individual_results.playtime between :starttime and :endtime
            --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
            --[individual] --[guest_skip] and guest = 0 -- ゲストなし
            --[friendly_fire] and same_team = 0
            --[team] and individual_results.name notnull
            --[player_name] and individual_results.name in (<<player_list>>) -- 対象プレイヤー
            --[search_word] and game_info.comment like :search_word
        group by
            individual_results.name
    """

    return (query_modification(sql))
