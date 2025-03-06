drop view if exists regulations;
create view if not exists regulations as
    select
        remarks.thread_ts,
        remarks.name as name,
        ifnull(team.name, '未所属') as team,
        group_concat(remarks.matter) as word,
        sum(words.ex_point) as ex_point,
        ifnull(words.type, 0) as type,
        game_info.guest_count,
        game_info.same_team
    from
        remarks
    left join member on
        member.name == remarks.name
    left join team on
        member.team_id == team.id
    left join words on
        words.word == remarks.matter
    join game_info on
        game_info.ts == remarks.thread_ts
    where
        {regulation_where}
    group by
        remarks.thread_ts, remarks.name
;
