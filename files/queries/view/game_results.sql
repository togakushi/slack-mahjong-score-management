create view if not exists game_results as
    select
        datetime(result.playtime) as playtime,
        result.ts,
        -- 東家
            p1_name,
            ifnull(p1_team.name, '未所属') as p1_team,
            ifnull(p1.name not in (select name from member where id != 0), 1) as p1_guest,
            p1_rpoint,
            p1_rank,
            p1_point + ifnull(p1_regulations.ex_point, 0) as p1_point,
            case when p1_regulations.type = 0 then p1_regulations.word else null end as p1_grandslam,
            case when p1_regulations.type = 1 then p1_regulations.word else null end as p1_regulation,
            p1_regulations.type as p1_type,
            p1_regulations.ex_point as p1_ex_point,
        -- 南家
            p2_name,
            ifnull(p2_team.name, '未所属') as p2_team,
            ifnull(p2.name not in (select name from member where id != 0), 1) as p2_guest,
            p2_rpoint,
            p2_rank,
            p2_point + ifnull(p2_regulations.ex_point, 0) as p2_point,
            case when p2_regulations.type = 0 then p2_regulations.word else null end as p2_grandslam,
            case when p2_regulations.type = 1 then p2_regulations.word else null end as p2_regulation,
            p2_regulations.type as p2_type,
            p2_regulations.ex_point as p2_ex_point,
        -- 西家
            p3_name,
            ifnull(p3_team.name, '未所属') as p3_team,
            ifnull(p3.name not in (select name from member where id != 0), 1) as p3_guest,
            p3_rpoint,
            p3_rank,
            p3_point + ifnull(p3_regulations.ex_point, 0) as p3_point,
            case when p3_regulations.type = 0 then p3_regulations.word else null end as p3_grandslam,
            case when p3_regulations.type = 1 then p3_regulations.word else null end as p3_regulation,
            p3_regulations.type as p3_type,
            p3_regulations.ex_point as p3_ex_point,
        -- 北家
            p4_name,
            ifnull(p4_team.name, '未所属') as p4_team,
            ifnull(p4.name not in (select name from member where id != 0), 1) as p4_guest,
            p4_rpoint,
            p4_rank,
            p4_point + ifnull(p4_regulations.ex_point, 0) as p4_point,
            case when p4_regulations.type = 0 then p4_regulations.word else null end as p4_grandslam,
            case when p4_regulations.type = 1 then p4_regulations.word else null end as p4_regulation,
            p4_regulations.type as p4_type,
            p4_regulations.ex_point as p4_ex_point,
        -- 情報
            deposit,
            date(result.playtime, '-12 hours') as collection_daily,
            result.comment,
            game_info.guest_count,
            game_info.same_team,
            result.rule_version
    from
        result
    join game_info on game_info.ts = result.ts
    left join member as p1 on p1.name = result.p1_name
    left join member as p2 on p2.name = result.p2_name
    left join member as p3 on p3.name = result.p3_name
    left join member as p4 on p4.name = result.p4_name
    left join team as p1_team on p1.team_id = p1_team.id
    left join team as p2_team on p2.team_id = p2_team.id
    left join team as p3_team on p3.team_id = p3_team.id
    left join team as p4_team on p4.team_id = p4_team.id
    left join regulations as p1_regulations on p1_regulations.thread_ts = result.ts and p1_regulations.name = result.p1_name
    left join regulations as p2_regulations on p2_regulations.thread_ts = result.ts and p2_regulations.name = result.p2_name
    left join regulations as p3_regulations on p3_regulations.thread_ts = result.ts and p3_regulations.name = result.p3_name
    left join regulations as p4_regulations on p4_regulations.thread_ts = result.ts and p4_regulations.name = result.p4_name
;
