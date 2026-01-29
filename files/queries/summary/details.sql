--- summary.details
select
    --[not_search_word] results.playtime,
    --[search_word] game_info.comment as playtime,
    --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.guest = 0 then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
    --[team] results.team as name,
    --[individual] results.guest,
    --[team] 0 as guest,
    seat,
    rpoint,
    rank,
    --[individual] point,
    --[team] team_point as point,
    yakuman,
    --[individual] regulation,
    --[team] team_regulation as regulation,
    --[individual] ex_point,
    --[team] team_ex_point as ex_point,
    --[individual] remarks,
    --[team] team_remarks as remarks,
    game_info.guest_count,
    game_info.same_team
from
    individual_results as results
join game_info
    on game_info.ts = results.ts
where
    results.mode = :mode and seat <= :mode
    and results.rule_version in (<<rule_list>>)
    and results.playtime between :starttime and :endtime
    --[separate] and results.source = :source
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
    --[individual] --[guest_skip] and results.guest = 0 -- ゲストナシ
    --[individual] --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
    --[team] and results.team != '未所属' -- 未所属除外
    --[team] --[friendly_fire] and game_info.same_team = 0
    --[team] --[player_name] and results.team in (<<player_list>>) -- 対象チーム
    --[search_word] and game_info.comment like :search_word
order by
    results.playtime
;
