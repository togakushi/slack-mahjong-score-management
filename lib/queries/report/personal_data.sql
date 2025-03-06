-- report.personal_data
select
    <<collection>>,
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
from
    individual_results
where
    rule_version = :rule_version
    and playtime between :starttime and :endtime
    and name = :player_name
<<group by>>
order by
    collection_daily desc
;
