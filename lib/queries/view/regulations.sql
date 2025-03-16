drop view if exists regulations;
create view if not exists regulations as
    select
        remarks.thread_ts,
        remarks.name as name,
        ifnull(team.name, '未所属') as team,
        case when member.id isnull then 1 else 0 end as guest,
        group_concat(remarks.matter) as word,
        words.type,
        sum(ifnull(words.ex_point, 0)) as ex_point
    from
        remarks
    left join member on
        member.name == remarks.name
    left join team on
        member.team_id == team.id
    left join words on
        words.word == remarks.matter
    where
        {regulation_where}
    group by
        remarks.thread_ts, remarks.name
;
