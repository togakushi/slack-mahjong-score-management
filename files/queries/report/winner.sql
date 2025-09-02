-- report.winner
with target_data as (
    select
        substr(collection_daily, 1, 7) as collection,
        --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] case when results.guest = 0 then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
        --[team] results.team as name,
        point
    from
        individual_results as results
    join game_info on
        game_info.ts = results.ts
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストナシ
        --[individual] --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[team] and results.team != '未所属' -- 未所属除外
        --[team] --[friendly_fire] and game_info.same_team = 0
        --[team] --[player_name] and results.team in (<<player_list>>) -- 対象チーム
        --[search_word] and game_info.comment like :search_word
    order by
        results.playtime desc
    --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
)
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
    from
        target_data
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
