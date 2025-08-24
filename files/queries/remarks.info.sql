-- remarks.info
select
    datetime(remarks.thread_ts, "unixepoch") as playtime,
    --[individual] --[unregistered_replace] case when member.id isnull then :guest_name else remarks.name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when member.id isnull then remarks.name || '(<<guest_mark>>)' else remarks.name end as name, -- ゲスト無効
    --[team] ifnull(team.name, "未所属") as name,
    remarks.matter,
    ifnull(words.type, :undefined_word) as type,
    words.ex_point
from
    remarks
join game_info on
    game_info.ts = remarks.thread_ts
left join words on
    remarks.matter = words.word
left join member on
    member.name = remarks.name
left join team on
    team.id = member.team_id
where
    game_info.rule_version = :rule_version
    and playtime between :starttime and :endtime -- 検索範囲
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
    --[individual] --[player_name] and remarks.name in (<<player_list>>) -- 対象プレイヤー
    --[team] --[friendly_fire] and game_info.same_team = 0
    --[team] --[player_name] and team.team in (<<player_list>>) -- 対象チーム
    --[search_word] and game_info.comment like :search_word
;
