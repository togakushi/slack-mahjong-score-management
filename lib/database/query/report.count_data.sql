-- report.count_data()
select
    min(game_count) as 開始,
    max(game_count) as 終了,
    count() as ゲーム数,
    round(sum(point), 1) as 通算ポイント,
    round(avg(point), 1) as 平均ポイント,
    count(rank = 1 or NULL) as "1位",
    round(cast(count(rank = 1 or NULL) AS real) / cast(count() as real) * 100, 2) as "1位率",
    count(rank = 2 or NULL) as "2位",
    round(cast(count(rank = 2 or NULL) AS real) / cast(count() as real) * 100, 2) as "2位率",
    count(rank = 3 or NULL) as "3位",
    round(cast(count(rank = 3 or NULL) AS real) / cast(count() as real) * 100, 2) as "3位率",
    count(rank = 4 or NULL) as "4位",
    round(cast(count(rank = 4 or NULL) AS real) / cast(count() as real) * 100, 2) as "4位率",
    round(avg(rank), 2) AS 平均順位,
    count(rpoint < -1 or NULL) as トビ,
    round(cast(count(rpoint < -1 OR NULL) AS real) / cast(count() as real) * 100, 2) as トビ率
from (
    select
        (row_number() over (order by game_count desc) - 1) / :interval as interval,
        game_count, rank, point, rpoint
    from (
        select
            row_number() over (order by playtime) as game_count,
            rank, point, rpoint
        from
            individual_results
        where
            rule_version = :rule_version
            and name = :player_name
    )
    order by
        game_count desc
)
group by interval
;
