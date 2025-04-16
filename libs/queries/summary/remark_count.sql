-- summary.remark_count
with target_data as (
    select
        member.name as name,
        team.name as team,
        case when member.id isnull then 1 else 0 end as guest,
        matter,
        words.type,
        ex_point
    from
        remarks
    left join member on
        member.name == remarks.name
    left join team on
        member.team_id == team.id
    left join words on
        words.word == remarks.matter
    left join game_info on
        game_info.ts == remarks.thread_ts
    where
        rule_version = :rule_version
        and playtime between :starttime and :endtime
        --[individual] --[player_name] and remarks.name in (<<player_list>>) -- 対象プレイヤー
        --[team] --[player_name] and team.name in (<<player_list>>) -- 対象チーム
        --[friendly_fire] and same_team = 0
        --[search_word] and comment like :search_word
        <<where_string>>
)
select
    --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when guest = 0 or name = :guest_name then name else name || '(<<guest_mark>>)' end as name, -- ゲスト無効
    --[team] team as name,
    matter,
    count() as count,
    type,
    sum(ex_point) as ex_point
from
    target_data
group by
    name, matter
;
