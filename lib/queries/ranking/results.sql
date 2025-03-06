-- ranking.results
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
;
