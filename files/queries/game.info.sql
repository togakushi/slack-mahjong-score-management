-- game.info
with game_data as (
    select
        game_info.playtime as playtime,
        --[group_length] substr(game_info.comment, 1, :group_length) as comment,
        --[not_group_length] game_info.comment as comment,
        individual_results.name as name,
        individual_results.team as team
    from
        game_info
    join individual_results on
        individual_results.playtime = game_info.playtime
    where
        game_info.rule_version = :rule_version
        and game_info.playtime between :starttime and :endtime
        --[separate] and game_info.source = :source
        --[individual] --[guest_not_skip] and guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[friendly_fire] and same_team = 0
        --[search_word] and game_info.comment like :search_word
    order by
        game_info.playtime asc
)
select
    game_count as count,
    first_game, last_game,
    first_comment, last_comment,
    unique_name, unique_team
from (
    select
        dense_rank() over(order by playtime, name, team) as no,
        (select count(distinct playtime) from game_data) as game_count,
        first_value(playtime) over(order by playtime asc) as first_game,
        last_value(playtime) over(order by playtime desc) as last_game,
        first_value(comment) over(order by playtime asc) as first_comment,
        last_value(comment) over(order by playtime desc) as last_comment,
        (select count(distinct name) from game_data) as unique_name,
        (select count(distinct team) from game_data) as unique_team
    from
        game_data
)
order by
    no desc
limit 1
;
