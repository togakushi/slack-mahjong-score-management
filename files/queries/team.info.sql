-- team.info.sql
select
    -- team.id,
    team.name as 'チーム名',
    group_concat(member.name) as '所属メンバー'
from
    team
left join member on
    member.team_id = team.id
group by
    team.name
order by
    team.id
;
