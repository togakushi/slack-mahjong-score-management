-- summary.remarks.sql
with target_data as (
    select
        datetime(remarks.thread_ts, 'unixepoch') as playtime,
        remarks.name as name,
        ifnull(team.name, '未所属') as team,
        case when member.id isnull then 1 else 0 end as guest,
        remarks.matter as matter,
        ifnull(words.type, :undefined_word) as type,
        ifnull(words.ex_point, 0) as ex_point,
        game_info.rule_version
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
)
select
    playtime,
    --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when guest = 0 or name = :guest_name then name else name || '(<<guest_mark>>)' end as name, -- ゲスト無効
    --[team] team as name,
    guest,
    matter,
    type,
    ex_point
from
    target_data
where
    rule_version = :rule_version
    and playtime between :starttime and :endtime
    --[individual] --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
    --[team] --[player_name] and team in (<<player_list>>) -- 対象チーム
    --[friendly_fire] and same_team = 0
    --[search_word] and comment like :search_word
;
