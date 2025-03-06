-- ranking.ratings
select
    playtime,
    p1_name, p1_rank,
    p2_name, p2_rank,
    p3_name, p3_rank,
    p4_name, p4_rank
from
    game_results
where
    rule_version = :rule_version
    and playtime between :starttime and :endtime
;
