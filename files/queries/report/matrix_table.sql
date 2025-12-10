-- report.matrix_table
select
    --[not_search_word] results.playtime,
    --[search_word] game_info.comment as playtime,
    --[unregistered_replace] case when p1_guest = 0 then p1_name else :guest_name end as p1_name, -- ゲスト有効
    --[unregistered_not_replace] p1_name, -- ゲスト無効
    --[team] p1_team as p1_name,
    p1_rank,
    --[unregistered_replace] case when p2_guest = 0 then p2_name else :guest_name end as p2_name, -- ゲスト有効
    --[unregistered_not_replace] p2_name, -- ゲスト無効
    --[team] p2_team as p2_name,
    p2_rank,
    --[unregistered_replace] case when p3_guest = 0 then p3_name else :guest_name end as p3_name, -- ゲスト有効
    --[unregistered_not_replace] p3_name, -- ゲスト無効
    --[team] p3_team as p3_name,
    p3_rank,
    --[unregistered_replace] case when p4_guest = 0 then p4_name else :guest_name end as p4_name, -- ゲスト有効
    --[unregistered_not_replace] p4_name, -- ゲスト無効
    --[team] p4_team as p4_name,
    p4_rank
from
    game_results as results
join game_info on
    game_info.ts = results.ts
where
    results.rule_version = :rule_version
    and results.playtime between :starttime and :endtime
    --[separate] and results.source = :source
    --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
    --[team] and game_info.same_team = 0
    --[team] and p1_team notnull and p2_team notnull and p3_team notnull and p4_team notnull
    --[search_word] and game_info.comment like :search_word
;
