-- report.results_list
with target_data as (
    select
        --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] case when results.guest = 0 or results.name = :guest_name then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
        --[team] results.name as name,
        point,
        rpoint,
        rank,
        gs_count
    from
        --[individual] individual_results as results
        --[team] team_results as results
    join game_info on
        game_info.ts == results.ts
    left join grandslam on
        grandslam.thread_ts == results.ts
        and grandslam.name == results.name
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストナシ
        --[team] --[friendly_fire] and game_info.same_team = 0
        --[team] and team_id notnull -- 未所属除外
        --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[search_word] and game_info.comment like :search_word
    order by
        results.playtime desc
    --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
)
select
    name,
    count() as "game",
    replace(printf("%+.1f pt", round(sum(point), 1)), "-", "▲") as "total_mix",
    round(sum(point), 1) as "point_sum",
    replace(printf("%+.1f pt", round(avg(point), 1)), "-", "▲") as "avg_mix",
    round(avg(point), 1) as "point_avg",
    count(rank = 1 or null) as "1st_count",
    cast(count(rank = 1 or null) as real) / count() * 100 as "1st(%)",
    printf("%3d (%6.2f%%)",
        count(rank = 1 or null),
        round(cast(count(rank = 1 or null) as real) / count() * 100, 2)
    ) as "1st_mix",
    count(rank = 2 or null) as "2nd_count",
    cast(count(rank = 2 or null) as real) / count() * 100 as "2nd(%)",
    printf("%3d (%6.2f%%)",
        count(rank = 2 or null),
        round(cast(count(rank = 2 or null) as real) / count() * 100, 2)
    ) as "2nd_mix",
    count(rank = 3 or null) as "3rd_count",
    cast(count(rank = 3 or null) as real) / count() * 100 as "3rd(%)",
    printf("%3d (%6.2f%%)",
        count(rank = 3 or null),
        round(cast(count(rank = 3 or null) as real) / count() * 100, 2)
    ) as "3rd_mix",
    count(rank = 4 or null) as "4th_count",
    cast(count(rank = 4 or null) as real) / count() * 100 as "4th(%)",
    printf("%3d (%6.2f%%)",
        count(rank = 4 or null),
        round(cast(count(rank = 4 or null) AS real) / count() * 100, 2)
    ) as "4th_mix",
    printf("%.2f", avg(rank)) as "rank_avg",
    count(rpoint < 0 or null) as "flying_count",
    cast(count(rpoint < 0 or null) as real) / count() * 100 as "flying(%)",
    printf("%3d (%6.2f%%)",
        count(rpoint < 0 or null),
        round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2)
    ) as "flying_mix",
    ifnull(sum(gs_count), 0) as "yakuman_count",
    cast(ifnull(sum(gs_count), 0) as real) / count() * 100 as "yakuman(%)",
    printf("%3d (%6.2f%%)",
        ifnull(sum(gs_count), 0),
        round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2)
    ) as "yakuman_mix"
from
    target_data
group by
    name
having
    count() >= :stipulated -- 規定打数
order by
    sum(point) desc
;
