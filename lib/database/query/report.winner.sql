-- report.winner()
select
    collection,
    max(case when rank = 1 then name end) as name1,
    max(case when rank = 1 then total end) as point1,
    max(case when rank = 2 then name end) as name2,
    max(case when rank = 2 then total end) as point2,
    max(case when rank = 3 then name end) as name3,
    max(case when rank = 3 then total end) as point3,
    max(case when rank = 4 then name end) as name4,
    max(case when rank = 4 then total end) as point4,
    max(case when rank = 5 then name end) as name5,
    max(case when rank = 5 then total end) as point5
from (
    select
        collection,
        rank() over (partition by collection order by round(sum(point), 1) desc) as rank,
        name,
        round(sum(point), 1) as total
    from (
        select
            substr(collection_daily, 1, 7) as collection,
            --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
            --[unregistered_not_replace] name, -- ゲスト無効
            point
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
            --[guest_skip] and guest = 0 -- ゲストなし
            --[friendly_fire] and same_team = 0
            --[search_word] and comment like :search_word
    )
    group by
        name, collection
    having
        count() >= :stipulated -- 規定打数
)
group by
    collection
order by
    collection desc
;
