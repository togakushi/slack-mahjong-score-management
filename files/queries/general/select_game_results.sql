--
select
    ts,
    p1_name, p1_str,
    p2_name, p2_str,
    p3_name, p3_str,
    p4_name, p4_str,
    comment,
    rule_version
from
    result where ts=:ts
;
