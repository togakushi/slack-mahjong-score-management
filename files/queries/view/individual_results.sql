create view if not exists individual_results as
with
    yakuman_table as (
        select
            thread_ts, name, group_concat(word) as word
        from
            regulations
        where
            type = 0
        group by
            thread_ts, name
    ),
    memo_table as (
        select
            thread_ts, name, group_concat(word) as word
        from
            regulations
        where
            type = 1
        group by
            thread_ts, name
    ),
    regulation_table as (
        select
            thread_ts, name, sum(ex_point) as ex_point, group_concat(word) as word
        from
            regulations
        where
            type = 2
        group by
            thread_ts, name
    ),
    them_regulation_table as (
        select
            thread_ts, name, sum(ex_point) as ex_point, group_concat(word) as word
        from
            regulations
        where
            type in (2, 3)
        group by
            thread_ts, name
    ),
    remarks_table as (
        select
            thread_ts, name, group_concat(word) as word
        from
            regulations
        where
            type in (0, 1, 2)
        group by
            thread_ts, name
    ),
    them_remarks_table as (
        select
            thread_ts, name, group_concat(word) as word
        from
            regulations
        where
            type in (0, 1, 2, 3)
        group by
            thread_ts, name
    )
select * from (
    -- 東家
    select
        datetime(playtime) as playtime,
        ts,
        1 as seat,
        p1_name as name,
        ifnull(team.name, '未所属') as team,
        p1_name not in (select name from member where id != 0) as guest,
        p1_rpoint as rpoint,
        p1_rank as rank,
        p1_point as original_point,
        -- メモ
        yakuman_table.word as yakuman,
        memo_table.word as memo,
        -- 個人戦レギュレーション
        regulation_table.word as regulation,
        regulation_table.ex_point as ex_point,
        p1_point + ifnull(regulation_table.ex_point, 0) as point,
        remarks_table.word as remarks,
        -- チーム戦レギュレーション
        them_regulation_table.word as them_regulation,
        them_regulation_table.ex_point as them_ex_point,
        p1_point + ifnull(them_regulation_table.ex_point, 0) as team_point,
        them_remarks_table.word as them_remarks,
        --
        date(playtime, '-<time_adjust> hours') as collection_daily,
        rule_version,
        comment,
        source
    from
        result
    left join member
        on member.name = result.p1_name
    left join team
        on team.id = member.team_id
    left join yakuman_table
        on yakuman_table.thread_ts = result.ts
        and yakuman_table.name = result.p1_name
    left join memo_table
        on memo_table.thread_ts = result.ts
        and memo_table.name = result.p1_name
    left join regulation_table
        on regulation_table.thread_ts = result.ts
        and regulation_table.name = result.p1_name
    left join them_regulation_table
        on them_regulation_table.thread_ts = result.ts
        and them_regulation_table.name = result.p1_name
    left join remarks_table
        on remarks_table.thread_ts = result.ts
        and remarks_table.name = result.p1_name
    left join them_remarks_table
        on them_remarks_table.thread_ts = result.ts
        and them_remarks_table.name = result.p1_name
    -- 南家
    union all select
        datetime(playtime),
        ts,
        2 as seat,
        p2_name,
        ifnull(team.name, '未所属'),
        p2_name not in (select name from member where id != 0),
        p2_rpoint,
        p2_rank,
        p2_point,
        -- メモ
        yakuman_table.word,
        memo_table.word,
        -- 個人戦レギュレーション
        regulation_table.word,
        regulation_table.ex_point,
        p2_point + ifnull(regulation_table.ex_point, 0),
        remarks_table.word,
        -- チーム戦レギュレーション
        them_regulation_table.word,
        them_regulation_table.ex_point,
        p2_point + ifnull(them_regulation_table.ex_point, 0),
        them_remarks_table.word,
        --
        date(playtime, '-<time_adjust> hours'),
        rule_version,
        comment,
        source
    from
        result
    left join member
        on member.name = result.p2_name
    left join team
        on team.id = member.team_id
    left join yakuman_table
        on yakuman_table.thread_ts = result.ts
        and yakuman_table.name = result.p2_name
    left join memo_table
        on memo_table.thread_ts = result.ts
        and memo_table.name = result.p2_name
    left join regulation_table
        on regulation_table.thread_ts = result.ts
        and regulation_table.name = result.p2_name
    left join them_regulation_table
        on them_regulation_table.thread_ts = result.ts
        and them_regulation_table.name = result.p2_name
    left join remarks_table
        on remarks_table.thread_ts = result.ts
        and remarks_table.name = result.p2_name
    left join them_remarks_table
        on them_remarks_table.thread_ts = result.ts
        and them_remarks_table.name = result.p2_name
    -- 西家
    union all select
        datetime(playtime),
        ts,
        3 as seat,
        p3_name,
        ifnull(team.name, '未所属'),
        p3_name not in (select name from member where id != 0),
        p3_rpoint,
        p3_rank,
        p3_point,
        -- メモ
        yakuman_table.word,
        memo_table.word,
        -- 個人戦レギュレーション
        regulation_table.word,
        regulation_table.ex_point,
        p3_point + ifnull(regulation_table.ex_point, 0),
        remarks_table.word,
        -- チーム戦レギュレーション
        them_regulation_table.word,
        them_regulation_table.ex_point,
        p3_point + ifnull(them_regulation_table.ex_point, 0),
        them_remarks_table.word,
        --
        date(playtime, '-<time_adjust> hours'),
        rule_version,
        comment,
        source
    from
        result
    left join member
        on member.name = result.p3_name
    left join team
        on team.id = member.team_id
    left join yakuman_table
        on yakuman_table.thread_ts = result.ts
        and yakuman_table.name = result.p3_name
    left join memo_table
        on memo_table.thread_ts = result.ts
        and memo_table.name = result.p3_name
    left join regulation_table
        on regulation_table.thread_ts = result.ts
        and regulation_table.name = result.p3_name
    left join them_regulation_table
        on them_regulation_table.thread_ts = result.ts
        and them_regulation_table.name = result.p3_name
    left join remarks_table
        on remarks_table.thread_ts = result.ts
        and remarks_table.name = result.p3_name
    left join them_remarks_table
        on them_remarks_table.thread_ts = result.ts
        and them_remarks_table.name = result.p3_name
    -- 北家
    union all select
        datetime(playtime),
        ts,
        4 as seat,
        p4_name,
        ifnull(team.name, '未所属'),
        p4_name not in (select name from member where id != 0),
        p4_rpoint,
        p4_rank,
        p4_point,
        -- メモ
        yakuman_table.word,
        memo_table.word,
        -- 個人戦レギュレーション
        regulation_table.word,
        regulation_table.ex_point,
        p4_point + ifnull(regulation_table.ex_point, 0),
        remarks_table.word,
        -- チーム戦レギュレーション
        them_regulation_table.word,
        them_regulation_table.ex_point,
        p4_point + ifnull(them_regulation_table.ex_point, 0),
        them_remarks_table.word,
        --
        date(playtime, '-<time_adjust> hours'),
        rule_version,
        comment,
        source
    from
        result
    left join member
        on member.name = result.p4_name
    left join team
        on team.id = member.team_id
    left join yakuman_table
        on yakuman_table.thread_ts = result.ts
        and yakuman_table.name = result.p4_name
    left join memo_table
        on memo_table.thread_ts = result.ts
        and memo_table.name = result.p4_name
    left join regulation_table
        on regulation_table.thread_ts = result.ts
        and regulation_table.name = result.p4_name
    left join them_regulation_table
        on them_regulation_table.thread_ts = result.ts
        and them_regulation_table.name = result.p4_name
    left join remarks_table
        on remarks_table.thread_ts = result.ts
        and remarks_table.name = result.p4_name
    left join them_remarks_table
        on them_remarks_table.thread_ts = result.ts
        and them_remarks_table.name = result.p4_name
)
order by ts, seat
;
