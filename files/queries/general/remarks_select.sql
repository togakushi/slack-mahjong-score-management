--
select
    thread_ts,
    event_ts,
    name,
    matter,
    source
from
    remarks
join result on
    result.ts = remarks.thread_ts
where
    thread_ts >= ?
    and source like ?
;
