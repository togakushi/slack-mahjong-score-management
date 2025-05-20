drop view if exists individual_results;
create view if not exists individual_results as
select * from (
    select
        datetime(playtime) as playtime,
        ts,
        1 as seat,
        p1_name as name,
        p1_rpoint as rpoint,
        p1_rank as rank,
        p1_point + ifnull(ex_point, 0) as point,
        grandslam,
        ifnull(ex_point, 0) as ex_point,
        p1_name not in (select name from member) as guest,
        date(result.playtime, '-12 hours') as collection_daily,
        rule_version,
        comment
    from
        result
    left join
        member on member.name = result.p1_name
    left join
        grandslam on grandslam.thread_ts == result.ts
        and grandslam.name = result.p1_name
    left join
        regulations on regulations.thread_ts == result.ts
        and regulations.name == result.p1_name
    group by ts, seat
    union all select
        datetime(playtime),
        ts,
        2 as seat,
        p2_name,
        p2_rpoint,
        p2_rank,
        p2_point + ifnull(ex_point, 0),
        grandslam,
        ifnull(ex_point, 0),
        p2_name not in (select name from member),
        date(result.playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join
        member on member.name = result.p2_name
    left join
        grandslam on grandslam.thread_ts == result.ts
        and grandslam.name = result.p2_name
    left join
        regulations on regulations.thread_ts == result.ts
        and regulations.name == result.p2_name
    group by ts, seat
    union all select
        datetime(playtime),
        ts,
        3 as seat,
        p3_name,
        p3_rpoint,
        p3_rank,
        p3_point + ifnull(ex_point, 0),
        grandslam,
        ifnull(ex_point, 0),
        p3_name not in (select name from member),
        date(result.playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join
        member on member.name = result.p3_name
    left join
        grandslam on grandslam.thread_ts == result.ts
        and grandslam.name = result.p3_name
    left join
        regulations on regulations.thread_ts == result.ts
        and regulations.name == result.p3_name
    group by ts, seat
    union all select
        datetime(playtime),
        ts,
        4 as seat,
        p4_name,
        p4_rpoint,
        p4_rank,
        p4_point + ifnull(ex_point, 0),
        grandslam,
        ifnull(ex_point, 0),
        p4_name not in (select name from member),
        date(result.playtime, '-12 hours'),
        rule_version,
        comment
    from
        result
    left join
        member on member.name = result.p4_name
    left join
        grandslam on grandslam.thread_ts == result.ts
        and grandslam.name = result.p4_name
    left join
        regulations on regulations.thread_ts == result.ts
        and regulations.name == result.p4_name
    group by ts, seat
)
order by ts, seat
;
