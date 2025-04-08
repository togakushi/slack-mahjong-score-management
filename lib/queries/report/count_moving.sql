-- report.count_moving
select
    interval,
    row_number() over (partition by interval) as game_no,
    total_count,
    playtime,
    round(sum(point) over moving, 1) as point_sum,
    round(avg(rank) over moving, 2) as rank_avg,
    rpoint * 100 as rpoint
from (
    select
        <<Calculation Formula>> as interval,
        total_count, playtime, rank, point, rpoint
    from (
        select
            row_number() over (order by playtime) as total_count,
            playtime, rank, point, rpoint
        from
            --[individual] individual_results as results
            --[team] team_results as results
        where
            rule_version = :rule_version
            and name = :player_name
    )
    order by
        total_count desc
)
window
    moving as (partition by interval order by total_count)
order by
    total_count
;
