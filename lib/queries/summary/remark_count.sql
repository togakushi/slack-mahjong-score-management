-- summary.remark_count
select
    --[individual] remarks.name,
    --[team] team.name as name,
    matter,
    count() as count,
    type,
    sum(ex_point) as ex_point,
    guest_count,
    same_team
from
    remarks
left join member on
    member.name == remarks.name
left join team on
    member.team_id == team.id
join game_info on
    game_info.ts == remarks.thread_ts
left join words on
    words.word == remarks.matter
where
    rule_version = :rule_version
    and playtime between :starttime and :endtime
    --[individual] --[player_name] and remarks.name in (<<player_list>>) -- 対象プレイヤー
    --[team] --[player_name] and team.name in (<<player_list>>) -- 対象チーム
    --[friendly_fire] and same_team = 0
    --[search_word] and comment like :search_word
    <<where_string>>
group by
    --[individual] remarks.name, matter
    --[team] team.name, matter
;
