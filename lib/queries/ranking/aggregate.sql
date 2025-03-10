with target_data as (
	select
		--[individual] --[unregistered_replace] case when guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
		--[individual] --[unregistered_not_replace] case when guest = 0 or results.name = :guest_name then results.name else results.name || '(<<guest_mark>>)' end as name, -- ゲスト無効
		--[team] results.name as name,
		point,
		rpoint,
		rank,
		gs_count
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
    name,
	count() as game_count,
	count(point > 0 or null) as win,
	count(point < 0 or null) as lose,
	count(point = 0 or null) as draw,

	count(rank = 1 or null) as rank1,
	round(cast(count(rank = 1 or null) as real) / count(), 4) as rank1_rate,
	count(rank = 2 or null) as rank2,
	round(cast(count(rank = 2 or null) as real) / count(), 4) as rank2_rate,
	count(rank = 3 or null) as rank3,
	round(cast(count(rank = 3 or null) as real) / count(), 4) as rank3_rate,
	count(rank = 4 or null) as rank4,
	round(cast(count(rank = 4 or null) as real) / count(), 4) as rank4_rate,
	round(avg(rank), 2) as rank_avg,
    printf("%d+%d+%d+%d=%d",
        count(rank = 1 or null),
        count(rank = 2 or null),
        count(rank = 3 or null),
        count(rank = 4 or null),
        count()
    ) as rank_dist,

	count(rpoint < 0 or null) as flying,
	round(cast(count(rpoint < 0 or null) as real) / count(), 4) as flying_rate,

	count(rank <= 2 or null) as top2,
	round(cast(count(rank <= 2 or null) as real) / count(), 4) as top2_rate,
	count(rank <= 3 or null) as top3,
	round(cast(count(rank <= 3 or null) as real) / count(), 4) as top3_rate,

	count(rank >= 2 or null) as low,
	round(cast(count(rank >= 2 or null) as real) / count(), 4) as low_rate,
	count(rank >= 3 or null) as low2,
	round(cast(count(rank >= 3 or null) as real) / count(), 4) as low2_rate,

    ifnull(sum(gs_count), 0) as gs_count,
	round(cast(ifnull(sum(gs_count), 0) as real) / count(), 4) as gs_rate,

	sum(point) as point_sum,
	round(avg(point), 1) as point_avg,
	round(max(point), 1) as point_max,
	round(min(point), 1) as point_min,

	max(rpoint) * 100 as rpoint_max,
	min(rpoint) * 100 as rpoint_min,
	cast(avg(rpoint) as integer) * 100 as rpoint_avg
from
	target_data
group by
    name
having
	game_count >= :stipulated -- 規定打数
order by
	game_count desc
;
