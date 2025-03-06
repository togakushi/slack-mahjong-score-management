--- summary.details
select
    --[not_search_word] results.playtime,
    --[search_word] game_info.comment as playtime,
    --[team] results.name as name,
    --[individual] results.name as name,
    --[individual] guest,
    game_info.guest_count,
    game_info.same_team,
    seat,
    rpoint,
    rank,
    point,
    grandslam.grandslam as grandslam,
    regulations.word as regulation,
    regulations.ex_point,
    regulations.type as type,
    --[not_group_length] game_info.comment
    --[group_length] substr(game_info.comment, 1, :group_length) as comment
from
    --[individual] individual_results as results
    --[team] team_results as results
join game_info on
    game_info.ts == results.ts
left join grandslam on
    grandslam.thread_ts == results.ts
    --[individual] and grandslam.name == results.name
    --[team] and grandslam.team == results.name
left join regulations on
    regulations.thread_ts == results.ts
    --[individual] and regulations.name == results.name
    --[team] and regulations.team == results.name
where
    results.rule_version = :rule_version
    and results.playtime between :starttime and :endtime
    --[search_word] and game_info.comment like :search_word
    --[friendly_fire] and game_info.same_team = 0
order by
    results.playtime
;
