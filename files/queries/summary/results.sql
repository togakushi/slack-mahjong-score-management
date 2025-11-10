-- summary.results
select
    name,
    count() as count,
    count(point > 0 or null) as 'win',
    count(point < 0 or null) as 'lose',
    count(point = 0 or null) as 'draw',
    count(rank = 1 or null) as '1位',
    round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as '1位率',
    count(rank = 2 or null) as '2位',
    round(cast(count(rank = 2 or null) as real) / count() * 100, 2) as '2位率',
    count(rank = 3 or null) as '3位',
    round(cast(count(rank = 3 or null) as real) / count() * 100, 2) as '3位率',
    count(rank = 4 or null) as '4位',
    round(cast(count(rank = 4 or null) as real) / count() * 100, 2) as '4位率',
    printf("%d-%d-%d-%d (%.2f)",
        count(rank = 1 or null),
        count(rank = 2 or null),
        count(rank = 3 or null),
        count(rank = 4 or null),
        round(avg(rank), 2)
    ) as '順位分布',
    round(avg(rpoint) * 100, 1) as '平均最終素点',
    round(sum(point), 1) as '通算ポイント',
    round(avg(point), 1) as '平均ポイント',
    round(avg(rank), 2) as '平均順位',
    count(rpoint < 0 or null) as 'トビ',
    round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as 'トビ率',
    ifnull(sum(gs_count), 0) as '役満和了',
    round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2) as '役満和了率',
    round((avg(rpoint) - :origin_point) * 100, 1) as '平均収支',
    round((avg(rpoint) - :return_point) * 100, 1) as '平均収支2',
    count(rank <= 2 or null) as '連対',
    round(cast(count(rank <= 2 or null) as real) / count() * 100, 2) as '連対率',
    round(cast(count(rank >= 3 or null) as real) / count() * 100, 2) as '逆連対率',
    count(rank <= 3 or null) as 'ラス回避',
    round(cast(count(rank <= 3 or null) as real) / count() * 100, 2) as 'ラス回避率',
    -- 座席順位分布
    count(seat = 1 and rank = 1 or null) as '東家-1位',
    count(seat = 1 and rank = 2 or null) as '東家-2位',
    count(seat = 1 and rank = 3 or null) as '東家-3位',
    count(seat = 1 and rank = 4 or null) as '東家-4位',
    round(avg(case when seat = 1 then rank end), 2) as '東家-平均順位',
    sum(case when seat = 1 then gs_count end) as '東家-役満和了',
    count(seat = 1 and rpoint < 0 or null) as '東家-トビ',
    printf("%d+%d+%d+%d=%d",
        count(seat = 1 and rank = 1 or null),
        count(seat = 1 and rank = 2 or null),
        count(seat = 1 and rank = 3 or null),
        count(seat = 1 and rank = 4 or null),
        count(seat = 1 or null)
    ) as '東家-順位分布',
    count(seat = 2 and rank = 1 or null) as '南家-1位',
    count(seat = 2 and rank = 2 or null) as '南家-2位',
    count(seat = 2 and rank = 3 or null) as '南家-3位',
    count(seat = 2 and rank = 4 or null) as '南家-4位',
    round(avg(case when seat = 2 then rank end), 2) as '南家-平均順位',
    sum(case when seat = 2 then gs_count end) as '南家-役満和了',
    count(seat = 2 and rpoint < 0 or null) as '南家-トビ',
    printf("%d+%d+%d+%d=%d",
        count(seat = 2 and rank = 1 or null),
        count(seat = 2 and rank = 2 or null),
        count(seat = 2 and rank = 3 or null),
        count(seat = 2 and rank = 4 or null),
        count(seat = 2 or null)
    ) as '南家-順位分布',
    count(seat = 3 and rank = 1 or null) as '西家-1位',
    count(seat = 3 and rank = 2 or null) as '西家-2位',
    count(seat = 3 and rank = 3 or null) as '西家-3位',
    count(seat = 3 and rank = 4 or null) as '西家-4位',
    round(avg(case when seat = 3 then rank end), 2) as '西家-平均順位',
    sum(case when seat = 3 then gs_count end) as '西家-役満和了',
    count(seat = 3 and rpoint < 0 or null) as '西家-トビ',
    printf("%d+%d+%d+%d=%d",
        count(seat = 3 and rank = 1 or null),
        count(seat = 3 and rank = 2 or null),
        count(seat = 3 and rank = 3 or null),
        count(seat = 3 and rank = 4 or null),
        count(seat = 3 or null)
    ) as '西家-順位分布',
    count(seat = 4 and rank = 1 or null) as '北家-1位',
    count(seat = 4 and rank = 2 or null) as '北家-2位',
    count(seat = 4 and rank = 3 or null) as '北家-3位',
    count(seat = 4 and rank = 4 or null) as '北家-4位',
    round(avg(case when seat = 4 then rank end), 2) as '北家-平均順位',
    sum(case when seat = 4 then gs_count end) as '北家-役満和了',
    count(seat = 4 and rpoint < 0 or null) as '北家-トビ',
    printf("%d+%d+%d+%d=%d",
        count(seat = 4 and rank = 1 or null),
        count(seat = 4 and rank = 2 or null),
        count(seat = 4 and rank = 3 or null),
        count(seat = 4 and rank = 4 or null),
        count(seat = 4 or null)
    ) as '北家-順位分布',
    min(playtime) as 'first_game',
    max(playtime) as 'last_game'
from (
    select
        results.playtime,
        --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] case when results.guest = 0 then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
        --[team] results.team as name,
        rpoint,
        rank,
        point,
        seat,
        grandslam,
        ifnull(count, 0) as gs_count
    from
        individual_results as results
    join game_info on
        game_info.ts = results.ts
    left join regulations as grandslam
        on
            grandslam.type = 0
            and grandslam.thread_ts = results.ts
            --[individual] and grandslam.name = results.name
            --[team] and grandslam.name = results.team
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストなし
        --[friendly_fire] and game_info.same_team = 0
        --[team] and results.team != "未所属" -- 未所属除外
        --[individual] --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[team] --[player_name] and results.team in (<<player_list>>) -- 対象チーム
        --[search_word] and game_info.comment like :search_word
    order by
        results.playtime desc
)
group by
    name
having
    count() >= :stipulated -- 規定打数
order by
    sum(point) desc
;
