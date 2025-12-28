--
update result set
    p1_name = :p1_name, p1_str = :p1_str, p1_rpoint = :p1_rpoint, p1_rank = :p1_rank, p1_point = :p1_point,
    p2_name = :p2_name, p2_str = :p2_str, p2_rpoint = :p2_rpoint, p2_rank = :p2_rank, p2_point = :p2_point,
    p3_name = :p3_name, p3_str = :p3_str, p3_rpoint = :p3_rpoint, p3_rank = :p3_rank, p3_point = :p3_point,
    p4_name = :p4_name, p4_str = :p4_str, p4_rpoint = :p4_rpoint, p4_rank = :p4_rank, p4_point = :p4_point,
    deposit = :deposit, comment = :comment, source = :source, mode = :mode
where ts=:ts
;
