-- summary.gamedata
select
    --[not_collection] --[not_group_by] count() over moving as count,
    --[not_collection] --[group_by] sum(count) over moving as count,
    --[collection] sum(count) over moving as count,
    --[not_collection] replace(playtime, "-", "/") as playtime,
    --[collection] replace(collection, "-", "/") as playtime,
    name,
    rank,
    point,
    round(sum(point) over moving, 1) as point_sum,
    round(avg(point) over moving, 1) as point_avg,
    round(avg(rank) over moving, 2) as rank_avg,
    comment
from (
    select
        --[collection] count() as count,
        --[not_collection] --[group_by] count() as count,
        results.playtime,
        --[collection_daily] collection_daily as collection,
        --[collection_monthly] substr(collection_daily, 1, 7) as collection,
        --[collection_yearly] substr(collection_daily, 1, 4) as collection,
        --[collection_all] '' as collection,
        --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
        --[individual] --[unregistered_not_replace] case when guest = 0 then name else name || '(<<guest_mark>>)' end as name, -- ゲスト無効
        --[team] team as name,
        --[not_collection] rank,
        --[collection] round(avg(rank), 2) as rank,
        --[not_collection] --[not_group_by] point,
        --[not_collection] --[group_by] round(sum(point), 1) as point,
        --[collection] round(sum(point), 1) as point,
        game_info.guest_count,
        --[not_group_length] game_info.comment
        --[group_length] substr(game_info.comment, 1, :group_length) as comment
    from
        individual_results as results
    join
        game_info on results.ts = game_info.ts
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
        --[individual] --[guest_skip] and results.guest = 0 -- ゲストナシ
        --[individual] --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
        --[team] and results.team != '未所属' -- 未所属除外
        --[team] --[friendly_fire] and game_info.same_team = 0
        --[team] --[player_name] and results.team in (<<player_list>>) -- 対象チーム
        --[search_word] and game_info.comment like :search_word
    --[not_collection] --[group_by] group by -- コメント集約
    --[not_collection] --[group_by]     --[not_comment] collection_daily, name
    --[not_collection] --[group_by]     --[comment] game_info.comment, name
    --[not_collection] --[group_by]     --[group_length] substr(game_info.comment, 1, :group_length), name
    --[collection] group by
    --[collection_daily]     collection_daily, name -- 日次集計
    --[collection_monthly]     substr(collection_daily, 1, 7), name -- 月次集計
    --[collection_yearly]     substr(collection_daily, 1, 4), name -- 年次集計
    --[collection_all]     name -- 全体集計
    order by
        --[not_collection] results.playtime desc
        --[collection_daily] collection_daily desc
        --[collection_monthly] substr(collection_daily, 1, 7) desc
        --[collection_yearly] substr(collection_daily, 1, 4) desc
        --[collection_all] collection_daily desc
)
window
    --[not_collection] moving as (partition by name order by playtime)
    --[collection] moving as (partition by name order by collection)
order by
    --[not_collection] playtime, name
    --[collection] collection, name
;
