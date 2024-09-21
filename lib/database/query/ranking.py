
import global_value as g
from lib.database.common import query_modification


def record_count():
    """
    連続連対などの記録をカウントするSQLを生成
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

    if g.opt.team:
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))
