drop view if exists game_results;
create view if not exists game_results as
    select
        datetime(result.playtime) as playtime, result.ts,
        p1_name, ifnull(p1_team.name, '未所属') as p1_team,
        p1.name isnull as p1_guest, p1_rpoint, p1_rank, p1_point,
        p2_name, ifnull(p2_team.name, '未所属') as p2_team,
        p2.name isnull as p2_guest, p2_rpoint, p2_rank, p2_point,
        p3_name, ifnull(p3_team.name, '未所属') as p3_team,
        p3.name isnull as p3_guest, p3_rpoint, p3_rank, p3_point,
        p4_name, ifnull(p4_team.name, '未所属') as p4_team,
        p4.name isnull as p4_guest, p4_rpoint, p4_rank, p4_point,
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
;
