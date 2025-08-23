-- game.info
select
    count() as count,
    --[group_length] substr(first_comment, 1, :group_length) as first_comment,
    --[group_length] substr(last_comment, 1, :group_length) as last_comment,
    --[not_group_length] first_comment, last_comment,
    first_game, last_game
from (
    select
        first_value(playtime) over(order by playtime asc) as first_game,
        last_value(playtime) over(order by playtime asc) as last_game,
        first_value(comment) over(order by playtime asc) as first_comment,
        last_value(comment) over(order by playtime asc) as last_comment
    from
        game_info
    where
        rule_version = :rule_version
        and playtime between :starttime and :endtime -- 検索範囲
        --[individual] --[guest_not_skip] and guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[friendly_fire] and same_team = 0
        --[search_word] and comment like :search_word
    order by
        playtime desc
);
