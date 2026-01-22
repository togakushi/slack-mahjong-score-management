--record.info.sql
with base_tbl as (
    select
        *
    from (
        select
            playtime,
            --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
            --[individual] --[unregistered_not_replace] case when guest = 0 then name else name || '(<<guest_mark>>)' end as name, -- ゲスト無効
            --[team] team as name,
            guest,
            seat,
            rank,
            mode,
            rule_version,
            sum(guest) over (partition by playtime) as guest_count,
            count(*) over (partition by playtime, team) as same_team
        from
            individual_results
    )
    where
        mode = :mode and seat <= :mode
        and rule_version in (<<rule_list>>)
        and playtime between :starttime and :endtime
        --[separate] and source = :source
        --[individual] --[guest_not_skip] and guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and guest = 0 -- ゲストナシ
        --[individual] --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
        --[team] and name != '未所属' -- 未所属除外
        --[team] --[friendly_fire] and same_team != 0
        --[team] --[player_name] and name in (<<player_list>>) -- 対象チーム
        --[search_word] and comment like :search_word
),
all_tbl as (
    select playtime, name, seat, rank from base_tbl
    union all
    select playtime, name, 0 as seat, rank from base_tbl
),
expanded_tbl as (
    select playtime, name, seat, rank, 'top1'  as cond, rank = 1 as ok from all_tbl
    union all
    select playtime, name, seat, rank, 'top2'  as cond, rank <= 2 as ok from all_tbl
    union all
    select playtime, name, seat, rank, 'top3'  as cond, rank <= 3 as ok from all_tbl
    union all
    select playtime, name, seat, rank, 'lose2'  as cond, rank >= 2 as ok from all_tbl
    union all
    select playtime, name, seat, rank, 'lose3'  as cond, rank >= 3 as ok from all_tbl
    union all
    select playtime, name, seat, rank, 'lose4'  as cond, rank = 4 as ok from all_tbl
),
grouped_tbl as (
    select
        playtime, name, seat, cond, ok,
        sum(case when ok = 0 then 1 else 0 end) over (partition by name, seat, cond order by playtime) as grp
    from
        expanded_tbl
    order by
        playtime, seat, name
),
max_streak_tbl as (
    select
        name, seat, cond, max(cnt) as max_streak
    from (
        select
            name,
            seat,
            cond,
            grp,
            count(*) as cnt
        from
            grouped_tbl
        where
            ok = 1
        group by
            name, seat, cond ,grp
    )
    group by
        name, seat, cond
),
current_streak_tbl as (
    select
        g.name,
        g.seat,
        g.cond,
        case
            when latest.ok = 0 then 0
            else count(*)
        end as cur_streak
    from
        grouped_tbl as g
    join (
        select
            name, seat, cond, grp, ok
        from (
            select
                *,
                row_number() over (partition by name, seat, cond order by playtime desc) as rn
            from
                grouped_tbl
        )
        where rn = 1
    ) as latest
      on g.name = latest.name
     and g.seat = latest.seat
     and g.cond = latest.cond
     and g.grp  = latest.grp
    where
        g.ok = 1
    group by
        g.name, g.seat, g.cond, latest.ok
)
select
    m.name,
    case
        when m.seat = 1 then '東家'
        when m.seat = 2 then '南家'
        when m.seat = 3 then '西家'
        when m.seat = 4 then '北家'
        else '全体'
    end as seat,
    m.seat as id,
    ifnull(max(case when m.cond = 'top1'  then m.max_streak end), 0) as top1_max,
    ifnull(max(case when c.cond = 'top1'  then c.cur_streak end), 0) as top1_cur,
    ifnull(max(case when m.cond = 'top2'  then m.max_streak end), 0) as top2_max,
    ifnull(max(case when c.cond = 'top2'  then c.cur_streak end), 0) as top2_cur,
    ifnull(max(case when m.cond = 'top3'  then m.max_streak end), 0) as top3_max,
    ifnull(max(case when c.cond = 'top3'  then c.cur_streak end), 0) as top3_cur,
    ifnull(max(case when m.cond = 'lose2' then m.max_streak end), 0) as lose2_max,
    ifnull(max(case when c.cond = 'lose2' then c.cur_streak end), 0) as lose2_cur,
    ifnull(max(case when m.cond = 'lose3' then m.max_streak end), 0) as lose3_max,
    ifnull(max(case when c.cond = 'lose3' then c.cur_streak end), 0) as lose3_cur,
    ifnull(max(case when m.cond = 'lose4' then m.max_streak end), 0) as lose4_max,
    ifnull(max(case when c.cond = 'lose4' then c.cur_streak end), 0) as lose4_cur
from
    max_streak_tbl as m
left join current_streak_tbl as c
    on
        m.name = c.name
        and m.seat = c.seat
        and m.cond = c.cond
group by
    m.name, m.seat
;
