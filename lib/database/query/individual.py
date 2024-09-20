from lib.database.common import query_modification


def versus_matrix():
    """
    直接対戦結果を集計するSQLを生成
    """

    sql = """
        -- personal.versus_matrix()
        select
            my_name, vs_name,
            count() as game,
            count(my_rank < vs_rank or null) as win,
            count(my_rank > vs_rank or null) as lose,
            round(cast(count(my_rank < vs_rank or null) AS real) / count() * 100, 2) as 'win%',
            printf("%d 戦 %d 勝 %d 敗",
                count(),
                count(my_rank < vs_rank or null),
                count(my_rank > vs_rank or null)
            ) as results,
            round(sum(my_point),1 ) as my_point_sum,
            round(avg(my_point),1 ) as my_point_avg,
            round(sum(vs_point), 1) as vs_point_sum,
            round(avg(vs_point), 1) as vs_point_avg,
            round(avg(my_rpoint), 1) as my_rpoint_avg,
            round(avg(vs_rpoint), 1) as vs_rpoint_avg,
            count(my_rank = 1 or null) as my_1st,
            count(my_rank = 2 or null) as my_2nd,
            count(my_rank = 3 or null) as my_3rd,
            count(my_rank = 4 or null) as my_4th,
            round(avg(my_rank), 2) as my_rank_avg,
            printf("%d-%d-%d-%d",
                count(my_rank = 1 or null),
                count(my_rank = 2 or null),
                count(my_rank = 3 or null),
                count(my_rank = 4 or null)
            ) as my_rank_distr,
            count(vs_rank = 1 or null) as vs_1st,
            count(vs_rank = 2 or null) as vs_2nd,
            count(vs_rank = 3 or null) as vs_3rd,
            count(vs_rank = 4 or null) as vs_4th,
            round(avg(vs_rank), 2) as vs_rank_avg,
            printf("%d-%d-%d-%d",
                count(vs_rank = 1 or null),
                count(vs_rank = 2 or null),
                count(vs_rank = 3 or null),
                count(vs_rank = 4 or null)
            ) as vs_rank_distr
        from (
            select
                my.name as my_name,
                my.rank as my_rank,
                my.rpoint as my_rpoint,
                my.point as my_point,
                --[unregistered_replace] case when vs.guest = 0 then vs.name else :guest_name end as vs_name, -- ゲスト有効
                --[unregistered_not_replace] vs.name as vs_name, -- ゲスト無効
                vs.rank as vs_rank,
                vs.rpoint as vs_rpoint,
                vs.point as vs_point
            from
                individual_results my
            inner join
                individual_results vs
                    on (my.playtime = vs.playtime and my.name != vs.name)
            where
                my.rule_version = :rule_version
                and my.playtime between :starttime and :endtime
                and my.name = :player_name
                --[guest_not_skip] and vs.playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and vs.guest = 0 -- ゲストなし
                --[comment] and my.comment like :search_word
            order by
                my.playtime desc
        )
        group by
            my_name, vs_name
        order by
            game desc
    """

    return (query_modification(sql))
