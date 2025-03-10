-- ranking.record_count
with target_data as (
	select
        results.playtime,
		--[individual] --[unregistered_replace] case when guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
		--[individual] --[unregistered_not_replace] case when guest = 0 or results.name = :guest_name then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
		--[team] results.name as team,
		point,
		rpoint,
		rank
	from
		--[individual] individual_results as results
		--[team] team_results as results
	join game_info on
		game_info.ts == results.ts
	left join grandslam on
		grandslam.thread_ts == results.ts
		and grandslam.name == results.name
	where
		results.rule_version = :rule_version
		and results.playtime between :starttime and :endtime -- 検索範囲
		--[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
		--[individual] --[guest_skip] and guest = 0 -- ゲストナシ
		--[team] --[friendly_fire] and game_info.same_team = 0
		--[team] and team_id notnull -- 未所属除外
		--[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
		--[search_word] and game_info.comment like :search_word
)
select
    playtime,
    --[individual] name,
    --[team] team as name,
    rank as "順位",
    point as "獲得ポイント",
    rpoint as "最終素点"
from
    target_data
;
