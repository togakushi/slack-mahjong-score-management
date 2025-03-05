drop view if exists grandslam;
create view if not exists grandslam as
    select
        remarks.thread_ts,
        remarks.name,
        ifnull(team.name, '未所属') as team,
        group_concat(remarks.matter) as grandslam,
        count() as gs_count,
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
        {grandslam_where}
    group by
        remarks.thread_ts, remarks.name
;
