-- game.info
select
    game_count as count,
    first_game, last_game,
    --[group_length] substr(first_comment, 1, :group_length) as first_comment,
    --[group_length] substr(last_comment, 1, :group_length) as last_comment,
    --[not_group_length] first_comment, last_comment,
    unique_name, unique_team
from (
    select
        count(distinct game_info.playtime) as game_count,
        first_value(game_info.playtime) over(order by game_info.playtime asc) as first_game,
        last_value(game_info.playtime) over(order by game_info.playtime asc) as last_game,
        first_value(game_info.comment) over(order by game_info.playtime asc) as first_comment,
        last_value(game_info.comment) over(order by game_info.playtime asc) as last_comment,
        count(distinct individual_results.name) as unique_name,
        count(distinct individual_results.team) as unique_team
    from
        game_info
    join individual_results on
        individual_results.playtime = game_info.playtime
    where
        game_info.rule_version = :rule_version
        and game_info.playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[friendly_fire] and same_team = 0
        --[search_word] and game_info.comment like :search_word
    order by
        game_info.playtime desc
);
