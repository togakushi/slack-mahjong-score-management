-- summary.versus_matrix
with target_data as (
    select
        results.playtime,
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
        --[search_word] and game_info.comment like :search_word
)
select
    my_name, vs_name,
    count() as game,
    count(my_rank < vs_rank or null) as win,
    count(my_rank > vs_rank or null) as lose,
    round(cast(count(my_rank < vs_rank or null) AS real) / count() * 100, 2) as 'win%',
    printf("%d 戦 %d 勝 %d 敗",
        count(),
        count(my_rank < vs_rank or null),
        count(my_rank > vs_rank or null)
    ) as results,
    round(sum(my_point),1 ) as my_point_sum,
    round(avg(my_point),1 ) as my_point_avg,
    round(sum(vs_point), 1) as vs_point_sum,
    round(avg(vs_point), 1) as vs_point_avg,
    round(avg(my_rpoint), 1) as my_rpoint_avg,
    round(avg(vs_rpoint), 1) as vs_rpoint_avg,
    count(my_rank = 1 or null) as my_1st,
    count(my_rank = 2 or null) as my_2nd,
    count(my_rank = 3 or null) as my_3rd,
    count(my_rank = 4 or null) as my_4th,
    round(avg(my_rank), 2) as my_rank_avg,
    printf("%d-%d-%d-%d",
        count(my_rank = 1 or null),
        count(my_rank = 2 or null),
        count(my_rank = 3 or null),
        count(my_rank = 4 or null)
    ) as my_rank_distr,
    count(vs_rank = 1 or null) as vs_1st,
    count(vs_rank = 2 or null) as vs_2nd,
    count(vs_rank = 3 or null) as vs_3rd,
    count(vs_rank = 4 or null) as vs_4th,
    round(avg(vs_rank), 2) as vs_rank_avg,
    printf("%d-%d-%d-%d",
        count(vs_rank = 1 or null),
        count(vs_rank = 2 or null),
        count(vs_rank = 3 or null),
        count(vs_rank = 4 or null)
    ) as vs_rank_distr
from (
    select
        my.name as my_name,
        my.rank as my_rank,
        my.rpoint as my_rpoint,
        my.point as my_point,
        vs.name as vs_name,
        vs.rank as vs_rank,
        vs.rpoint as vs_rpoint,
        vs.point as vs_point
    from
        target_data as my
    inner join target_data as vs on
        my.playtime = vs.playtime and my.name != vs.name
    order by
        my.playtime desc
)
--[player_name] where my_name in (<<player_list>>) -- 対象プレイヤー
group by
    my_name, vs_name
order by
    game desc
;
