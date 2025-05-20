drop view if exists team_results;
create view if not exists team_results as
    select * from (
        select
            datetime(result.playtime) as playtime,
            result.ts,
            1 as seat,
            ifnull(team.name, '未所属') as name,
            team.id as team_id,
            result.p1_rpoint as rpoint,
            result.p1_rank as rank,
            round(result.p1_point, 1) + ifnull(regulations.ex_point, 0) as point,
            ifnull(regulations.ex_point, 0) as ex_point,
            date(result.playtime, '-12 hours') as collection_daily,
            result.rule_version,
            result.comment
        from
            result
        left join member on
            result.p1_name = member.name
        left join team on
            member.team_id = team.id
        left join regulations on
            regulations.thread_ts == result.ts
            and regulations.name == result.p1_name
        union all select
            datetime(result.playtime) as playtime,
            result.ts,
            2 as seat,
            ifnull(team.name, '未所属') as name,
            team.id as team_id,
            result.p2_rpoint as rpoint,
            result.p2_rank as rank,
            round(result.p2_point, 1) + ifnull(regulations.ex_point, 0) as point,
            ifnull(regulations.ex_point, 0) as ex_point,
            date(result.playtime, '-12 hours') as collection_daily,
            result.rule_version,
            result.comment
        from
            result
        left join member on
            result.p2_name = member.name
        left join team on
            member.team_id = team.id
        left join regulations on
            regulations.thread_ts == result.ts
            and regulations.name == result.p2_name
        union all select
            datetime(result.playtime) as playtime,
            result.ts,
            3 as seat,
            ifnull(team.name, '未所属') as name,
            team.id as team_id,
            result.p3_rpoint as rpoint,
            result.p3_rank as rank,
            round(result.p3_point, 1) + ifnull(regulations.ex_point, 0) as point,
            ifnull(regulations.ex_point, 0) as ex_point,
            date(result.playtime, '-12 hours') as collection_daily,
            result.rule_version,
            result.comment
        from
            result
        left join member on
            result.p3_name = member.name
        left join team on
            member.team_id = team.id
        left join regulations on
            regulations.thread_ts == result.ts
            and regulations.name == result.p3_name
        union all select
            datetime(result.playtime) as playtime,
            result.ts,
            4 as seat,
            ifnull(team.name, '未所属') as name,
            team.id as team_id,
            result.p4_rpoint as rpoint,
            result.p4_rank as rank,
            round(result.p4_point, 1) + ifnull(regulations.ex_point, 0) as point,
            ifnull(regulations.ex_point, 0) as ex_point,
            date(result.playtime, '-12 hours') as collection_daily,
            result.rule_version,
            result.comment
        from
            result
        left join member on
            result.p4_name = member.name
        left join team on
            member.team_id = team.id
        left join regulations on
            regulations.thread_ts == result.ts
            and regulations.name == result.p4_name
    )
    order by ts, seat
;
