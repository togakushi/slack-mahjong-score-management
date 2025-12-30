--
select
    rank, rpoint
from
    individual_results
where
    mode = :mode
    and rule_version in (<<rule_list>>)
    and name = :player_name
;
