drop view if exists individual_results;
create view if not exists individual_results as
select * from (
    -- 東家
    select
        datetime(playtime) as playtime,
        ts,
        1 as seat,
        p1_name as name,
        ifnull(team.name, '未所属') as team,
        p1_rpoint as rpoint,
        p1_rank as rank,
        p1_point + ifnull(ex_point, 0) as point,
        case when type == 0 then word else null end as grandslam,
        case when type == 1 then word else null end as regulation,
        ifnull(ex_point, 0) as ex_point,
        p1_name not in (select name from member where id != 0) as guest,
        date(playtime, '-12 hours') as collection_daily,
        rule_version,
        comment
    from
        result
    left join member
        on
            member.name = result.p1_name
    left join team
        on
            team.id = member.team_id
    left join regulations
        on
            regulations.thread_ts == result.ts
            and regulations.name == result.p1_name
    -- 南家
    union all select
        datetime(playtime),
        ts,
        2 as seat,
        p2_name,
        ifnull(team.name, '未所属'),
        p2_rpoint,
        p2_rank,
        p2_point + ifnull(ex_point, 0),
        case when type == 0 then word else null end,
        case when type == 1 then word else null end,
        ifnull(ex_point, 0),
        p2_name not in (select name from member where id != 0),
        date(playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join member
        on
            member.name = result.p2_name
    left join team
        on
            team.id = member.team_id
    left join regulations
        on
            regulations.thread_ts == result.ts
            and regulations.name == result.p2_name
    -- 西家
    union all select
        datetime(playtime),
        ts,
        3 as seat,
        p3_name,
        ifnull(team.name, '未所属'),
        p3_rpoint,
        p3_rank,
        p3_point + ifnull(ex_point, 0),
        case when type == 0 then word else null end,
        case when type == 1 then word else null end,
        ifnull(ex_point, 0),
        p3_name not in (select name from member where id != 0),
        date(playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join member
        on
            member.name = result.p3_name
    left join team
        on
            team.id = member.team_id
    left join regulations
        on
            regulations.thread_ts == result.ts
            and regulations.name == result.p3_name
    -- 北家
    union all select
        datetime(playtime),
        ts,
        4 as seat,
        p4_name,
        ifnull(team.name, '未所属'),
        p4_rpoint,
        p4_rank,
        p4_point + ifnull(ex_point, 0),
        case when type == 0 then word else null end,
        case when type == 1 then word else null end,
        ifnull(ex_point, 0),
        p4_name not in (select name from member where id != 0),
        date(playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join member
        on
            member.name = result.p4_name
    left join team
        on
            team.id = member.team_id
    left join regulations
        on
            regulations.thread_ts == result.ts
            and regulations.name == result.p4_name
)
order by ts, seat
;
