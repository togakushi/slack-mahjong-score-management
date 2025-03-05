-- summary.versus_matrix()
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
        --[individual] --[unregistered_replace] case when vs.guest = 0 then vs.name else :guest_name end as vs_name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] vs.name as vs_name, -- ゲスト無効
        --[team] vs.name as vs_name,
        vs.rank as vs_rank,
        vs.rpoint as vs_rpoint,
        vs.point as vs_point
    from
        --[individual] individual_results as my
        --[team] team_results as my
    join game_info on
        game_info.ts == my.ts
    inner join
        --[individual] individual_results as vs on
        --[team] team_results as vs on
            my.playtime = vs.playtime and my.name != vs.name
    where
        my.rule_version = :rule_version
        and my.playtime between :starttime and :endtime
        and my.name = :player_name
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[individual] --[guest_skip] and vs.guest = 0 -- ゲストなし
        --[friendly_fire] and game_info.same_team = 0
        --[team] and vs.name notnull
        --[comment] and my.comment like :search_word
    order by
        my.playtime desc
)
group by
    my_name, vs_name
order by
    game desc
;
