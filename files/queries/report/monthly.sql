-- report.monthly
select
    strftime('%Y-%m', collection_daily) as 集計月,
    count() / 4 as ゲーム数,
    replace(printf('%.1f pt', round(sum(point), 1)), '-', '▲') as 供託,
    count(rpoint < -1 or null) as '飛んだ人数(延べ)',
    printf('%.2f%',	round(cast(count(rpoint < -1 or null) as real) / cast(count() / 4 as real) * 100, 2)) as トビ終了率,
    replace(printf('%s', max(rpoint)), '-', '▲') as 最大素点,
    replace(printf('%s', min(rpoint)), '-', '▲') as 最小素点
from
    individual_results as results
where
    mode = :mode
    and rule_version in (<<rule_list>>)
    and playtime between :starttime and :endtime
    --[separate] and source = :source
    --[search_word] and comment like :search_word
group by
    strftime('%Y-%m', collection_daily)
order by
    strftime('%Y-%m', collection_daily) desc
;
