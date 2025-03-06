-- report.monthly
select
    substr(collection_daily, 1, 7) as 集計月,
    count() / 4 as ゲーム数,
    replace(printf("%.1f pt", round(sum(point), 1)), "-", "▲") as 供託,
    count(rpoint < -1 or null) as "飛んだ人数(延べ)",
    printf("%.2f%",	round(cast(count(rpoint < -1 or null) as real) / cast(count() / 4 as real) * 100, 2)) as トビ終了率,
    replace(printf("%s", max(rpoint)), "-", "▲") as 最大素点,
    replace(printf("%s", min(rpoint)), "-", "▲") as 最小素点
from
    individual_results
where
    rule_version = :rule_version
    and playtime between :starttime and :endtime
    --[search_word] and comment like :search_word
group by
    substr(collection_daily, 1, 7)
order by
    substr(collection_daily, 1, 7) desc
;
