-- ranking.record_count()
select
    results.playtime,
    --[individual] --[unregistered_replace] case when guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] results.name, -- ゲスト無効
    --[team] results.name,
    rank as "順位",
    point as "獲得ポイント",
    rpoint as "最終素点"
from
    --[individual] individual_results as results
    --[team] team_results as results
join game_info on
    game_info.ts == results.ts
where
    results.rule_version = :rule_version
    and results.playtime between :starttime and :endtime
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
    --[individual] --[guest_skip] and guest = 0 -- ゲストなし
    --[friendly_fire] and same_team = 0
    --[team] and results.name notnull
    --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
    --[search_word] and game_info.comment like :search_word
;
