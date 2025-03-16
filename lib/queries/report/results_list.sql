-- report.results_list
select
    name,
    count() as "game",
    replace(printf("%+.1f pt", round(sum(point), 1)), "-", "▲") as "total_mix",
    round(sum(point), 1) as "point_sum",
    replace(printf("%+.1f pt", round(avg(point), 1)), "-", "▲") as "avg_mix",
    round(avg(point), 1) as "point_avg",
    count(rank = 1 or null) as "1st_count",
    cast(count(rank = 1 or null) as real) / count() * 100 as "1st_%",
    printf("%3d (%6.2f%%)",
        count(rank = 1 or null),
        round(cast(count(rank = 1 or null) as real) / count() * 100, 2)
    ) as "1st_mix",
    count(rank = 2 or null) as "2nd_count",
    cast(count(rank = 2 or null) as real) / count() * 100 as "2nd_%",
    printf("%3d (%6.2f%%)",
        count(rank = 2 or null),
        round(cast(count(rank = 2 or null) as real) / count() * 100, 2)
    ) as "2nd_mix",
    count(rank = 3 or null) as "3rd_count",
    cast(count(rank = 3 or null) as real) / count() * 100 as "3rd_%",
    printf("%3d (%6.2f%%)",
        count(rank = 3 or null),
        round(cast(count(rank = 3 or null) as real) / count() * 100, 2)
    ) as "3rd_mix",
    count(rank = 4 or null) as "4th_count",
    cast(count(rank = 4 or null) as real) / count() * 100 as "4th_%",
    printf("%3d (%6.2f%%)",
        count(rank = 4 or null),
        round(cast(count(rank = 4 or null) AS real) / count() * 100, 2)
    ) as "4th_mix",
    printf("%.2f", avg(rank)) as "rank_avg",
    count(rpoint < 0 or null) as "flying_count",
    cast(count(rpoint < 0 or null) as real) / count() * 100 as "flying_%",
    printf("%3d (%6.2f%%)",
        count(rpoint < 0 or null),
        round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2)
    ) as "flying_mix",
    ifnull(sum(gs_count), 0) as "yakuman_count",
    cast(ifnull(sum(gs_count), 0) as real) / count() * 100 as "yakuman_%",
    printf("%3d (%6.2f%%)",
        ifnull(sum(gs_count), 0),
        round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2)
    ) as "yakuman_mix"
from (
    select
        results.playtime,
        --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] results.name, -- ゲスト無効
        --[team] results.name,
        rpoint,
        rank,
        point,
        gs_count
    from
        --[individual] individual_results as results
        --[team] team_results as results
    join game_info on
        game_info.ts == results.ts
    left join grandslam on
        grandslam.thread_ts == results.ts
        --[individual] and grandslam.name == results.name
        --[team] and grandslam.team == results.name
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストなし
        --[friendly_fire] and same_team = 0
        --[team] and results.name notnull
        --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[search_word] and game_info.comment like :search_word
    order by
        results.playtime desc
    --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
)
group by
    name
having
    count() >= :stipulated -- 規定打数
order by
    sum(point) desc
;
