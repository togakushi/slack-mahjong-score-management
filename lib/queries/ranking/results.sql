-- ranking.results
select
    --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.guest = 0 or results.name = :guest_name then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
    --[team] results.name as name,
    count() as count,
    printf("%d+%d+%d+%d=%d",
        count(rank = 1 or null),
        count(rank = 2 or null),
        count(rank = 3 or null),
        count(rank = 4 or null),
        count()
    ) as rank_distr,
    round(avg(rpoint) * 100, 1) as rpoint_avg,
    round(avg(rank), 2) as rank_avg
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
group by
    results.name
;
