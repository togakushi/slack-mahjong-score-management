--
select
    rank, rpoint
from
    individual_results
where
    rule_version = :rule_version
    and name = :player_name
;
