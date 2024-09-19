
from lib.database.common import query_modification


def record_count():
    """
    連続連対などの記録をカウントするSQLを生成
    """

    sql = """
        -- ranking.record_count()
        select
            individual_results.playtime,
            --[unregistered_replace] case when guest = 0 then name else :guest_name end as "プレイヤー名", -- ゲスト有効
            --[unregistered_not_replace] name as "プレイヤー名", -- ゲスト無効
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
            --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
            --[guest_skip] and guest = 0 -- ゲストなし
            --[friendly_fire] and same_team = 0
            --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
            --[search_word] and game_info.comment like :search_word
    """

    return (query_modification(sql))
