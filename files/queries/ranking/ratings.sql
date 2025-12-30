-- ranking.ratings
select
    results.playtime,
    --[individual] --[unregistered_not_replace] case when p1_guest = 0 then p1_name else p1_name || '(<<guest_mark>>)' end as p1_name, -- ゲスト無効
    --[individual] --[unregistered_replace] case when p1_guest = 0 then p1_name else :guest_name end as p1_name, -- ゲスト有効
    --[team] p1_team as p1_name,
    p1_rpoint, p1_point, p1_rank,
    --[individual] --[unregistered_not_replace] case when p2_guest = 0 then p2_name else p2_name || '(<<guest_mark>>)' end as p2_name, -- ゲスト無効
    --[individual] --[unregistered_replace] case when p2_guest = 0 then p2_name else :guest_name end as p2_name, -- ゲスト有効
    --[team] p2_team as p2_name,
    p2_rpoint, p2_point, p2_rank,
    --[individual] --[unregistered_not_replace] case when p3_guest = 0 then p3_name else p3_name || '(<<guest_mark>>)' end as p3_name, -- ゲスト無効
    --[individual] --[unregistered_replace] case when p3_guest = 0 then p3_name else :guest_name end as p3_name, -- ゲスト有効
    --[team] p3_team as p3_name,
    p3_rpoint, p3_point, p3_rank,
    --[individual] --[unregistered_not_replace] case when p4_guest = 0 then p4_name else p4_name || '(<<guest_mark>>)' end as p4_name, -- ゲスト無効
    --[individual] --[unregistered_replace] case when p4_guest = 0 then p4_name else :guest_name end as p4_name, -- ゲスト有効
    --[team] p4_team as p4_name,
    p4_rpoint, p4_point, p4_rank
from
    game_results as results
left join game_info on
    game_info.playtime = results.playtime
where
    results.mode = :mode
    and results.rule_version in (<<rule_list>>)
    and results.playtime between :starttime and :endtime
    --[separate] and results.source = :source
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
    --[search_word] and game_info.comment like :search_word
;
