
-- summary.total
with point_table as (
    select
        --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] name, -- ゲスト無効
        --[team] name as team,
        --[individual] guest,
        rpoint,
        point,
        ex_point,
        rank
    from
        --[individual] individual_results as results
        --[team] team_results as results
    join game_info on
        game_info.ts == results.ts
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and guest = 0 -- ゲストナシ
        --[team] --[friendly_fire] and game_info.same_team = 0
        --[team] and team_id notnull -- 未所属除外
        --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
        --[search_word] and game_info.comment like :search_word
),
point_summary as (
    select
        --[individual] name,
        --[individual] guest,
        --[team] team,
        count() as count,
        sum(point) as total_point,
        sum(ex_point) as ex_point,
        round(avg(point), 1) as avg_point,
        count(rank = 1 or null) as rank1,
        count(rank = 2 or null) as rank2,
        count(rank = 3 or null) as rank3,
        count(rank = 4 or null) as rank4,
        round(avg(rank), 2) as rank_avg,
        count(rpoint < 0 or null) as flying
    from
        point_table
    group by
        --[individual] name
        --[team] team
    having
        count >= :stipulated -- 規定打数
),
ranked_points as (
    select
        --[individual] name,
        --[individual] guest,
        --[team] team,
        count,
        total_point,
        ex_point,
        avg_point,
        rank1,
        rank2,
        rank3,
        rank4,
        rank_avg,
        flying,
        rank() over (order by total_point desc) as overall_ranking,
        lag(total_point) over (order by total_point desc) as prev_point,
        first_value(total_point) over (order by total_point desc) as top_point
    from point_summary
)
select
    overall_ranking as rank,
    --[individual] case
    --[individual]     when guest = 0 or name = :guest_name then name
    --[individual]     else name || '(<<guest_mark>>)'
    --[individual] end as name,
    --[team] team,
    count,
    round(cast(total_point as real), 1) as total_point,
    ex_point,
    round(cast(avg_point as real), 1) as avg_point,
    rank1,
    rank2,
    rank3,
    rank4,
    rank_avg,
    flying,
    round(cast(rank1 as real)/count*100,2) as rank1_rate,
    round(cast(rank2 as real)/count*100,2) as rank2_rate,
    round(cast(rank3 as real)/count*100,2) as rank3_rate,
    round(cast(rank4 as real)/count*100,2) as rank4_rate,
    round(cast(flying as real)/count*100,2) as flying_rate,
    printf("%d-%d-%d-%d (%.2f)",
        rank1,
        rank2,
        rank3,
        rank4,
        rank_avg
    ) as rank_distr1,
    printf("%d+%d+%d+%d=%d (%.2f)",
        rank1,
        rank2,
        rank3,
        rank4,
        count,
        rank_avg
    ) as rank_distr2,
    case
        when prev_point is null then null
        else abs(round(total_point - prev_point, 1))
    end as diff_from_above,
    case
        when total_point = top_point then null
        else round(top_point - total_point, 1)
    end as diff_from_top
from ranked_points
order by rank, count desc
;
