import global_value as g
from lib.database.common import query_modification


def monthly():
    """
    """

    sql = """
        -- report.monthly()
        select
            substr(collection_daily, 1, 7) as 集計月,
            count() / 4 as ゲーム数,
            replace(printf("%.1f pt", round(sum(point), 1)), "-", "▲") as 供託,
            count(rpoint < -1 or null) as "飛んだ人数(延べ)",
            printf("%.2f%",	round(cast(count(rpoint < -1 or null) as real) / cast(count() / 4 as real) * 100, 2)) as トビ終了率,
            replace(printf("%s", max(rpoint)), "-", "▲") as 最大素点,
            replace(printf("%s", min(rpoint)), "-", "▲") as 最小素点
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[search_word] and comment like :search_word
        group by
            substr(collection_daily, 1, 7)
        order by
            substr(collection_daily, 1, 7) desc
    """

    return (query_modification(sql))


def winner():
    """
    """

    sql = """
        -- report.winner()
        select
            collection,
            max(case when rank = 1 then name end) as name1,
            max(case when rank = 1 then total end) as point1,
            max(case when rank = 2 then name end) as name2,
            max(case when rank = 2 then total end) as point2,
            max(case when rank = 3 then name end) as name3,
            max(case when rank = 3 then total end) as point3,
            max(case when rank = 4 then name end) as name4,
            max(case when rank = 4 then total end) as point4,
            max(case when rank = 5 then name end) as name5,
            max(case when rank = 5 then total end) as point5
        from (
            select
                collection,
                rank() over (partition by collection order by round(sum(point), 1) desc) as rank,
                name,
                round(sum(point), 1) as total
            from (
                select
                    substr(collection_daily, 1, 7) as collection,
                    --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                    --[unregistered_not_replace] name, -- ゲスト無効
                    point
                from
                    individual_results
                where
                    rule_version = :rule_version
                    and playtime between :starttime and :endtime
                    --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                    --[guest_skip] and guest = 0 -- ゲストなし
                    --[friendly_fire] and same_team = 0
                    --[search_word] and comment like :search_word
            )
            group by
                name, collection
            having
                count() >= :stipulated -- 規定打数
        )
        group by
            collection
        order by
            collection desc
    """

    return (query_modification(sql))


def matrix_table():
    """
    対局対戦マトリックス表の元データを抽出するSQLを生成
    """

    sql = """
        -- report.matrix_table()
        select
            --[not_search_word] game_results.playtime,
            --[search_word] game_info.comment as playtime,
            --[unregistered_replace] case when p1_guest = 0 then p1_name else :guest_name end as p1_name, -- ゲスト有効
            --[unregistered_not_replace] p1_name, -- ゲスト無効
            --[team] p1_team as p1_name,
            p1_rank,
            --[unregistered_replace] case when p2_guest = 0 then p2_name else :guest_name end as p2_name, -- ゲスト有効
            --[unregistered_not_replace] p2_name, -- ゲスト無効
            --[team] p2_team as p2_name,
            p2_rank,
            --[unregistered_replace] case when p3_guest = 0 then p3_name else :guest_name end as p3_name, -- ゲスト有効
            --[unregistered_not_replace] p3_name, -- ゲスト無効
            --[team] p3_team as p3_name,
            p3_rank,
            --[unregistered_replace] case when p4_guest = 0 then p4_name else :guest_name end as p4_name, -- ゲスト有効
            --[unregistered_not_replace] p4_name, -- ゲスト無効
            --[team] p4_team as p4_name,
            p4_rank
        from
            game_results
        join game_info on
            game_info.ts == game_results.ts
        where
            game_results.rule_version = :rule_version
            and game_results.playtime between :starttime and :endtime
            --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
            --[team] and game_info.same_team = 0
            --[team] and p1_team notnull and p2_team notnull and p3_team notnull and p4_team notnull
            --[search_word] and game_info.comment like :search_word
    """

    return (query_modification(sql))


def personal_data(flag="M"):
    sql = """
        -- report.personal_data()
        select
            <<collection>>,
            count() as ゲーム数,
            round(sum(point), 1) as 通算ポイント,
            round(avg(point), 1) as 平均ポイント,
            count(rank = 1 or NULL) as "1位",
            round(cast(count(rank = 1 or NULL) AS real) / cast(count() as real) * 100, 2) as "1位率",
            count(rank = 2 or NULL) as "2位",
            round(cast(count(rank = 2 or NULL) AS real) / cast(count() as real) * 100, 2) as "2位率",
            count(rank = 3 or NULL) as "3位",
            round(cast(count(rank = 3 or NULL) AS real) / cast(count() as real) * 100, 2) as "3位率",
            count(rank = 4 or NULL) as "4位",
            round(cast(count(rank = 4 or NULL) AS real) / cast(count() as real) * 100, 2) as "4位率",
            round(avg(rank), 2) AS 平均順位,
            count(rpoint < -1 or NULL) as トビ,
            round(cast(count(rpoint < -1 OR NULL) AS real) / cast(count() as real) * 100, 2) as トビ率
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            and name = :player_name
        <<group by>>
        order by
            collection_daily desc
    """

    match flag:
        case "M":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 7) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    return (query_modification(sql))


def count_data():
    sql = """
        -- report.count_data()
        select
            min(game_count) as 開始,
            max(game_count) as 終了,
            count() as ゲーム数,
            round(sum(point), 1) as 通算ポイント,
            round(avg(point), 1) as 平均ポイント,
            count(rank = 1 or NULL) as "1位",
            round(cast(count(rank = 1 or NULL) AS real) / cast(count() as real) * 100, 2) as "1位率",
            count(rank = 2 or NULL) as "2位",
            round(cast(count(rank = 2 or NULL) AS real) / cast(count() as real) * 100, 2) as "2位率",
            count(rank = 3 or NULL) as "3位",
            round(cast(count(rank = 3 or NULL) AS real) / cast(count() as real) * 100, 2) as "3位率",
            count(rank = 4 or NULL) as "4位",
            round(cast(count(rank = 4 or NULL) AS real) / cast(count() as real) * 100, 2) as "4位率",
            round(avg(rank), 2) AS 平均順位,
            count(rpoint < -1 or NULL) as トビ,
            round(cast(count(rpoint < -1 OR NULL) AS real) / cast(count() as real) * 100, 2) as トビ率
        from (
            select
                (row_number() over (order by game_count desc) - 1) / :interval as interval,
                game_count, rank, point, rpoint
            from (
                select
                    row_number() over (order by playtime) as game_count,
                    rank, point, rpoint
                from
                    individual_results
                where
                    rule_version = :rule_version
                    and name = :player_name
            )
            order by
                game_count desc
        )
        group by interval
    """

    return (query_modification(sql))


def count_moving(interval=40):
    sql = """
        -- report.count_moving()
        select
            interval,
            row_number() over (partition by interval) as game_no,
            total_count,
            playtime,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(rank) over moving, 2) as rank_avg
        from (
            select
                <<Calculation Formula>> as interval,
                total_count, playtime, rank, point
            from (
                select
                    row_number() over (order by playtime) as total_count,
                    playtime, rank, point
                from
                    individual_results
                where
                    rule_version = :rule_version
                    and name = :player_name
            )
            order by
                total_count desc
        )
        window
            moving as (partition by interval order by total_count)
        order by
            total_count
    """

    if interval == 0:
        sql = sql.replace("<<Calculation Formula>>", ":interval")
    else:
        sql = sql.replace(
            "<<Calculation Formula>>",
            "(row_number() over (order by total_count desc) - 1) / :interval"
        )

    return (query_modification(sql))


def results_list():
    sql = """
        -- report.results_list()
        select
            name,
            count() as "game",
            replace(printf("%+.1f pt", round(sum(point), 1)), "-", "▲") as "total_mix",
            round(sum(point), 1) as "point_sum",
            replace(printf("%+.1f pt", round(avg(point), 1)), "-", "▲") as "avg_mix",
            round(avg(point), 1) as "point_avg",
            count(rank = 1 or null) as "1st_count",
            cast(count(rank = 1 or null) as real) / count() * 100 as "1st_%",
            printf("%3d (%6.2f%%)",
                count(rank = 1 or null),
                round(cast(count(rank = 1 or null) as real) / count() * 100, 2)
            ) as "1st_mix",
            count(rank = 2 or null) as "2nd_count",
            cast(count(rank = 2 or null) as real) / count() * 100 as "2nd_%",
            printf("%3d (%6.2f%%)",
                count(rank = 2 or null),
                round(cast(count(rank = 2 or null) as real) / count() * 100, 2)
            ) as "2nd_mix",
            count(rank = 3 or null) as "3rd_count",
            cast(count(rank = 3 or null) as real) / count() * 100 as "3rd_%",
            printf("%3d (%6.2f%%)",
                count(rank = 3 or null),
                round(cast(count(rank = 3 or null) as real) / count() * 100, 2)
            ) as "3rd_mix",
            count(rank = 4 or null) as "4th_count",
            cast(count(rank = 4 or null) as real) / count() * 100 as "4th_%",
            printf("%3d (%6.2f%%)",
                count(rank = 4 or null),
                round(cast(count(rank = 4 or null) AS real) / count() * 100, 2)
            ) as "4th_mix",
            avg(rank) as "rank_avg",
            count(rpoint < 0 or null) as "flying_count",
            cast(count(rpoint < 0 or null) as real) / count() * 100 as "flying_%",
            printf("%3d (%6.2f%%)",
                count(rpoint < 0 or null),
                round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2)
            ) as "flying_mix",
            ifnull(sum(gs_count), 0) as "yakuman_count",
            cast(ifnull(sum(gs_count), 0) as real) / count() * 100 as "yakuman_%",
            printf("%3d (%6.2f%%)",
                ifnull(sum(gs_count), 0),
                round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2)
            ) as "yakuman_mix"
        from (
            select
                individual_results.playtime,
                --[individual] --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                --[team] team_results.name,
                rpoint,
                rank,
                point,
                gs_count
            from
                individual_results
            join game_info on
                game_info.ts == individual_results.ts
            left join grandslam on
                grandslam.thread_ts == individual_results.ts
                --[individual] and grandslam.name == individual_results.name
                --[team] and grandslam.team == team_results.name
            where
                individual_results.rule_version = :rule_version
                and individual_results.playtime between :starttime and :endtime
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and same_team = 0
                --[team] and individual_results.name notnull
                --[player_name] and individual_results.name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and game_info.comment like :search_word
            order by
                individual_results.playtime desc
            --[recent] limit :target_count * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            sum(point) desc
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))
