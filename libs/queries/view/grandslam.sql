drop view if exists grandslam;
create view if not exists grandslam as
    select
        remarks.thread_ts,
        remarks.name as name,
        ifnull(team.name, '未所属') as team,
        case when member.id isnull then 1 else 0 end as guest,
        group_concat(remarks.matter) as grandslam,
        count() as gs_count
    from
        remarks
    left join member on
        member.name == remarks.name
    left join team on
        member.team_id == team.id
    left join words on
        words.word == remarks.matter
    where
        {grandslam_where}
    group by
        remarks.thread_ts, remarks.name
;
