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
        p1_point as p1_original,
        group_concat(case when x1_regulations.type = 2 then x1_regulations.word else null end) as p1_regulation,
        sum(case when x1_regulations.type = 2 then x1_regulations.ex_point else 0 end) as p1_ex_point,
        p1_point + sum(case when x1_regulations.type = 2 then x1_regulations.ex_point else 0 end) as p1_point,
        group_concat(case when x1_regulations.type = 3 then x1_regulations.word else null end) as t1_regulation,
        sum(case when x1_regulations.type = 3 then x1_regulations.ex_point else 0 end) as t1_ex_point,
        p1_point + sum(case when x1_regulations.type in (2, 3) then x1_regulations.ex_point else 0 end) as t1_point,
        group_concat(case when x1_regulations.type = 0 then x1_regulations.word else null end) as p1_yakuman,
        group_concat(case when x1_regulations.type = 1 then x1_regulations.word else null end) as p1_memo,
        group_concat(case when x1_regulations.type in (0, 1, 2) then x1_regulations.word else null end) as p1_remarks,
        group_concat(case when x1_regulations.type in (0, 1, 2, 3) then x1_regulations.word else null end) as t1_remarks,
        -- 南家
        p2_name,
        ifnull(p2_team.name, '未所属') as p2_team,
        ifnull(p2.name not in (select name from member where id != 0), 1) as p2_guest,
        p2_rpoint,
        p2_rank,
        p2_point as p2_original,
        group_concat(case when x2_regulations.type = 2 then x2_regulations.word else null end) as p2_regulation,
        sum(case when x2_regulations.type = 2 then x2_regulations.ex_point else 0 end) as p2_ex_point,
        p2_point + sum(case when x2_regulations.type = 2 then x2_regulations.ex_point else 0 end) as p2_point,
        group_concat(case when x2_regulations.type = 3 then x2_regulations.word else null end) as t2_regulation,
        sum(case when x2_regulations.type = 3 then x2_regulations.ex_point else 0 end) as t2_ex_point,
        p2_point + sum(case when x2_regulations.type in (2, 3) then x2_regulations.ex_point else 0 end) as t2_point,
        group_concat(case when x2_regulations.type = 0 then x2_regulations.word else null end) as p2_yakuman,
        group_concat(case when x2_regulations.type = 1 then x2_regulations.word else null end) as p2_memo,
        group_concat(case when x2_regulations.type in (0, 1, 2) then x2_regulations.word else null end) as p2_remarks,
        group_concat(case when x2_regulations.type in (0, 1, 2, 3) then x2_regulations.word else null end) as t2_remarks,
        -- 西家
        p3_name,
        ifnull(p3_team.name, '未所属') as p3_team,
        ifnull(p3.name not in (select name from member where id != 0), 1) as p3_guest,
        p3_rpoint,
        p3_rank,
        p3_point as p3_original,
        group_concat(case when x3_regulations.type = 2 then x3_regulations.word else null end) as p3_regulation,
        sum(case when x3_regulations.type = 2 then x3_regulations.ex_point else 0 end) as p3_ex_point,
        p3_point + sum(case when x3_regulations.type = 2 then x3_regulations.ex_point else 0 end) as p3_point,
        group_concat(case when x3_regulations.type = 3 then x3_regulations.word else null end) as t3_regulation,
        sum(case when x3_regulations.type = 3 then x3_regulations.ex_point else 0 end) as t3_ex_point,
        p3_point + sum(case when x3_regulations.type in (2, 3) then x3_regulations.ex_point else 0 end) as t3_point,
        group_concat(case when x3_regulations.type = 0 then x3_regulations.word else null end) as p3_yakuman,
        group_concat(case when x3_regulations.type = 1 then x3_regulations.word else null end) as p3_memo,
        group_concat(case when x3_regulations.type in (0, 1, 2) then x3_regulations.word else null end) as p3_remarks,
        group_concat(case when x3_regulations.type in (0, 1, 2, 3) then x3_regulations.word else null end) as t3_remarks,
        -- 北家
        p4_name,
        ifnull(p4_team.name, '未所属') as p4_team,
        ifnull(p4.name not in (select name from member where id != 0), 1) as p4_guest,
        p4_rpoint,
        p4_rank,
        p4_point as p4_original,
        group_concat(case when x4_regulations.type = 2 then x4_regulations.word else null end) as p4_regulation,
        sum(case when x4_regulations.type = 2 then x4_regulations.ex_point else 0 end) as p4_ex_point,
        p4_point + sum(case when x4_regulations.type = 2 then x4_regulations.ex_point else 0 end) as p4_point,
        group_concat(case when x4_regulations.type = 3 then x4_regulations.word else null end) as t4_regulation,
        sum(case when x4_regulations.type = 3 then x4_regulations.ex_point else 0 end) as t4_ex_point,
        p4_point + sum(case when x4_regulations.type in (2, 3) then x4_regulations.ex_point else 0 end) as t4_point,
        group_concat(case when x4_regulations.type = 0 then x4_regulations.word else null end) as p4_yakuman,
        group_concat(case when x4_regulations.type = 1 then x4_regulations.word else null end) as p4_memo,
        group_concat(case when x4_regulations.type in (0, 1, 2) then x4_regulations.word else null end) as p4_remarks,
        group_concat(case when x4_regulations.type in (0, 1, 2, 3) then x4_regulations.word else null end) as t4_remarks,
        -- 情報
        deposit,
        date(result.playtime, '-12 hours') as collection_daily,
        result.comment,
        game_info.guest_count,
        game_info.same_team,
        result.rule_version
    from
        result
    join game_info
        on game_info.ts = result.ts
    -- プレイヤー名
    left join member as p1
        on p1.name = result.p1_name
    left join member as p2
        on p2.name = result.p2_name
    left join member as p3
        on p3.name = result.p3_name
    left join member as p4
        on p4.name = result.p4_name
    -- チーム名
    left join team as p1_team
        on p1.team_id = p1_team.id
    left join team as p2_team
        on p2.team_id = p2_team.id
    left join team as p3_team
        on p3.team_id = p3_team.id
    left join team as p4_team
        on p4.team_id = p4_team.id
    -- メモ
    left join regulations as x1_regulations
        on x1_regulations.thread_ts = result.ts and x1_regulations.name = result.p1_name
    left join regulations as x2_regulations
        on x2_regulations.thread_ts = result.ts and x2_regulations.name = result.p2_name
    left join regulations as x3_regulations
        on x3_regulations.thread_ts = result.ts and x3_regulations.name = result.p3_name
    left join regulations as x4_regulations
        on x4_regulations.thread_ts = result.ts and x4_regulations.name = result.p4_name
    group by
        result.playtime
;
