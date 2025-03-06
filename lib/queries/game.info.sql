-- game.info
select
    count() as count,
    --[group_length] substr(first_comment, 1, :group_length) as first_comment,
    --[group_length] substr(last_comment, 1, :group_length) as last_comment,
    --[not_group_length] first_comment, last_comment,
    first_game, last_game
from (
    select
        first_value(results.playtime) over(order by results.ts asc) as first_game,
        last_value(results.playtime) over(order by results.ts asc) as last_game,
        first_value(game_info.comment) over(order by results.ts asc) as first_comment,
        last_value(game_info.comment) over(order by results.ts asc) as last_comment
    from
        --[individual] individual_results as results
        --[team] team_results as results
    join game_info on
        game_info.ts == results.ts
    where
        results.rule_version = :rule_version
        and results.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
        --[friendly_fire] and same_team = 0
        --[search_word] and game_info.comment like :search_word
    group by
        results.playtime
    order by
        results.playtime desc
);
