--
delete from
    remarks
where
    thread_ts = :thread_ts
    and event_ts = :event_ts
    and name = :name
    and matter = :matter
;
