-- game.info
with target_data as (
    select
        *
    from
        game_info
    where
        mode = :mode
        and rule_version in (<<rule_list>>)
        and playtime between :starttime and :endtime
        --[separate] and source = :source
        --[individual] --[guest_not_skip] and guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
        --[friendly_fire] and same_team = 0
        --[search_word] and comment like :search_word
)
select distinct
    (select count(distinct playtime) from target_data) as count,
    first_value(playtime) over (order by playtime rows between unbounded preceding and unbounded following) as first_game,
    last_value(playtime) over (order by playtime rows between unbounded preceding and unbounded following) as last_game,
    first_value(comment) over (order by playtime rows between unbounded preceding and unbounded following) as first_comment,
    last_value(comment) over (order by playtime rows between unbounded preceding and unbounded following) as last_comment
from
    target_data
;
