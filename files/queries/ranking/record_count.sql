-- ranking.record_count
with target_data as (
    select
        results.playtime,
        --[individual] --[unregistered_replace] case when results.guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] case when results.guest = 0 then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
        --[team] results.team as name,
        point,
        rpoint,
        rank
    from
        individual_results as results
    join game_info on
        game_info.ts == results.ts
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストナシ
        --[individual] --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[team] and results.team != '未所属' -- 未所属除外
        --[team] --[friendly_fire] and game_info.same_team = 0
        --[team] --[player_name] and results.team in (<<player_list>>) -- 対象チーム
        --[search_word] and game_info.comment like :search_word
)
select
    playtime,
    name,
    rank as "順位",
    point as "獲得ポイント",
    rpoint as "最終素点",
    count(*) over (partition by name) as count,
    max(point) over (partition by name) as point_max,
    min(point) over (partition by name) as point_min,
    max(rpoint) over (partition by name) as rpoint_max,
    min(rpoint) over (partition by name) as rpoint_min
from
    target_data
;
