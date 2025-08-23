--- summary.details2
select
    --[not_search_word] results.playtime,
    --[search_word] game_info.comment as playtime,
    -- 東家
    --[individual] --[unregistered_replace] case when results.p1_guest = 0 then results.p1_name else :guest_name end as p1_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p1_guest = 0 then results.p1_name else results.p1_name || '(<<guest_mark>>)' end as p1_name, -- ゲスト無効
    --[team] results.p1_team as p1_name,
    p1_rpoint,
    p1_rank,
    p1_point,
    p1_grandslam,
    -- 南家
    --[individual] --[unregistered_replace] case when results.p2_guest = 0 then results.p2_name else :guest_name end as p2_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p2_guest = 0 then results.p2_name else results.p2_name || '(<<guest_mark>>)' end as p2_name, -- ゲスト無効
    --[team] results.p2_team as p2_name,
    p2_rpoint,
    p2_rank,
    p2_point,
    p2_grandslam,
    -- 西家
    --[individual] --[unregistered_replace] case when results.p3_guest = 0 then results.p3_name else :guest_name end as p3_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p3_guest = 0 then results.p3_name else results.p3_name || '(<<guest_mark>>)' end as p3_name, -- ゲスト無効
    --[team] results.p3_team as p3_name,
    p3_rpoint,
    p3_rank,
    p3_point,
    p3_grandslam,
    -- 北家
    --[individual] --[unregistered_replace] case when results.p4_guest = 0 then results.p4_name else :guest_name end as p4_name, -- ゲスト有効
    --[individual] --[unregistered_not_replace] case when results.p4_guest = 0 then results.p4_name else results.p4_name || '(<<guest_mark>>)' end as p4_name, -- ゲスト無効
    --[team] results.p4_team as p4_name,
    p4_rpoint,
    p4_rank,
    p4_point,
    p4_grandslam,
    game_info.guest_count,
    game_info.same_team
from
    game_results as results
join game_info
    on
        game_info.ts == results.ts
where
    results.rule_version = :rule_version
    and results.playtime between :starttime and :endtime
    --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
    --[team] --[friendly_fire] and game_info.same_team = 0
    --[search_word] and game_info.comment like :search_word
order by
    results.playtime
;
