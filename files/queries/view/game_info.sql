create view if not exists game_info as
    select
        datetime(playtime) as playtime,
        ts,
        case when p1.id isnull then 1 else 0 END +
        case when p2.id isnull then 1 else 0 END +
        case when p3.id isnull then 1 else 0 END +
        case when p4.id isnull then 1 else 0 END as guest_count,
        case
            when p1.team_id = p2.team_id then 1
            when p1.team_id = p3.team_id then 1
            when p1.team_id = p4.team_id then 1
            when p2.team_id = p3.team_id then 1
            when p2.team_id = p4.team_id then 1
            when p3.team_id = p4.team_id then 1
            else 0
        end as same_team,
        comment,
        rule_version,
        source,
        mode
    from
        result
    left join member as p1
        on p1_name = p1.name
    left join member as p2
        on p2_name = p2.name
    left join member as p3
        on p3_name = p3.name
    left join member as p4
        on p4_name = p4.name
;
