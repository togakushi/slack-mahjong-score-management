--- summary.details2
select
    --[not_search_word] results.playtime,
    --[search_word] game_info.comment as playtime,
    -- 東家
    --[individual] --[unregistered_replace] case when results.p1_guest = 0 then results.p1_name else :guest_name end as p1_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p1_guest = 0 then results.p1_name else results.p1_name || '(<<guest_mark>>)' end as p1_name, -- ゲスト無効
    --[team] results.p1_team as p1_name,
    p1_rpoint * 100 as p1_rpoint,
    p1_rank,
    --[individual] p1_point,
    --[team] t1_point as p1_point,
    --[individual] p1_remarks,
    --[team] t1_remarks as p1_remarks,
    -- 南家
    --[individual] --[unregistered_replace] case when results.p2_guest = 0 then results.p2_name else :guest_name end as p2_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p2_guest = 0 then results.p2_name else results.p2_name || '(<<guest_mark>>)' end as p2_name, -- ゲスト無効
    --[team] results.p2_team as p2_name,
    p2_rpoint * 100 as p2_rpoint,
    p2_rank,
    --[individual] p2_point,
    --[team] t2_point as p2_point,
    --[individual] p2_remarks,
    --[team] t2_remarks as p2_remarks,
    -- 西家
    --[individual] --[unregistered_replace] case when results.p3_guest = 0 then results.p3_name else :guest_name end as p3_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p3_guest = 0 then results.p3_name else results.p3_name || '(<<guest_mark>>)' end as p3_name, -- ゲスト無効
    --[team] results.p3_team as p3_name,
    p3_rpoint * 100 as p3_rpoint,
    p3_rank,
    --[individual] p3_point,
    --[team] t3_point as p3_point,
    --[individual] p3_remarks,
    --[team] t3_remarks as p3_remarks,
    -- 北家
    --[individual] --[unregistered_replace] case when results.p4_guest = 0 then results.p4_name else :guest_name end as p4_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p4_guest = 0 then results.p4_name else results.p4_name || '(<<guest_mark>>)' end as p4_name, -- ゲスト無効
    --[team] results.p4_team as p4_name,
    p4_rpoint * 100 as p4_rpoint,
    p4_rank,
    --[individual] p4_point,
    --[team] t4_point as p4_point,
    --[individual] p4_remarks,
    --[team] t4_remarks as p4_remarks,
    game_info.guest_count,
    game_info.same_team
from
    game_results as results
join game_info
    on
        game_info.ts = results.ts
where
    results.rule_version = :rule_version
    and results.playtime between :starttime and :endtime
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
    --[team] --[friendly_fire] and game_info.same_team = 0
    --[search_word] and game_info.comment like :search_word
order by
    results.playtime
;
