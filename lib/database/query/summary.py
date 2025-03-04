from lib.database.common import query_modification


def gamedata():
    """通算ポイント推移/平均順位推移

    Returns:
        str: SQL
    """

    sql = """
        -- summary.gamedata()
        select
            --[not_collection] --[not_group_by] count() over moving as count,
            --[not_collection] --[group_by] sum(count) over moving as count,
            --[collection] sum(count) over moving as count,
            --[not_collection] replace(playtime, "-", "/") as playtime,
            --[collection] replace(collection, "-", "/") as playtime,
            --[team] name as team,
            --[individual] name,
            rank,
            point,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(point) over moving, 1) as point_avg,
            round(avg(rank) over moving, 2) as rank_avg,
            comment
        from (
            select
                --[collection] count() as count,
                --[not_collection] --[group_by] count() as count,
                results.playtime,
                --[collection_daily] collection_daily as collection,
                --[collection_monthly] substr(collection_daily, 1, 7) as collection,
                --[collection_yearly] substr(collection_daily, 1, 4) as collection,
                --[collection_all] "" as collection,
                --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] name, -- ゲスト無効
                --[team] name,
                --[not_collection] rank,
                --[collection] round(avg(rank), 2) as rank,
                --[not_collection] --[not_group_by] point,
                --[not_collection] --[group_by] round(sum(point), 1) as point,
                --[collection] round(sum(point), 1) as point,
                game_info.guest_count,
                --[not_group_length] game_info.comment
                --[group_length] substr(game_info.comment, 1, :group_length) as comment
            from
                --[individual] individual_results as results
                --[team] team_results as results
            join
                game_info on results.ts = game_info.ts
            where
                results.rule_version = :rule_version
                and results.playtime between :starttime and :endtime
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and game_info.same_team = 0
                --[individual] --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and game_info.comment like :search_word
            --[not_collection] --[group_by] group by -- コメント集約
            --[not_collection] --[group_by]     --[not_comment] collection_daily, name
            --[not_collection] --[group_by]     --[comment] game_info.comment, name
            --[not_collection] --[group_by]     --[group_length] substr(game_info.comment, 1, :group_length), name
            --[collection] group by
            --[collection_daily]     collection_daily, name -- 日次集計
            --[collection_monthly]     substr(collection_daily, 1, 7), name -- 月次集計
            --[collection_yearly]     substr(collection_daily, 1, 4), name -- 年次集計
            --[collection_all]     name -- 全体集計
            order by
                --[not_collection] results.playtime desc
                --[collection_daily] collection_daily desc
                --[collection_monthly] substr(collection_daily, 1, 7) desc
                --[collection_yearly] substr(collection_daily, 1, 4) desc
                --[collection_all] collection_daily desc
        )
        window
            --[not_collection] moving as (partition by name order by playtime)
            --[collection] moving as (partition by name order by collection)
        order by
            --[not_collection] playtime, name
            --[collection] collection, name
    """

    return (query_modification(sql))


def results():
    """成績集計

    Returns:
        str: SQL
    """

    sql = """
        -- summary.results()
        select
            --[team] name as name,
            --[individual] name,
            count() as count,
            count(point > 0 or null) as win,
            count(point < 0 or null) as lose,
            count(point = 0 or null) as draw,
            count(rank = 1 or null) as '1位',
            round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as '1位率',
            count(rank = 2 or null) as '2位',
            round(cast(count(rank = 2 or null) as real) / count() * 100, 2) as '2位率',
            count(rank = 3 or null) as '3位',
            round(cast(count(rank = 3 or null) as real) / count() * 100, 2) as '3位率',
            count(rank = 4 or null) as '4位',
            round(cast(count(rank = 4 or null) as real) / count() * 100, 2) as '4位率',
            printf("%d-%d-%d-%d (%.2f)",
                count(rank = 1 or null),
                count(rank = 2 or null),
                count(rank = 3 or null),
                count(rank = 4 or null),
                round(avg(rank), 2)
            ) as 順位分布,
            round(avg(rpoint) * 100, 1) as 平均最終素点,
            round(sum(point), 1) as 通算ポイント,
            round(avg(point), 1) as 平均ポイント,
            round(avg(rank), 2) as 平均順位,
            count(rpoint < 0 or null) as トビ,
            round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as トビ率,
            ifnull(sum(gs_count), 0) as 役満和了,
            round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100, 2) as 役満和了率,
            round((avg(rpoint) - :origin_point) * 100, 1) as 平均収支,
            round((avg(rpoint) - :return_point) * 100, 1) as 平均収支2,
            count(rank <= 2 or null) as 連対,
            round(cast(count(rank <= 2 or null) as real) / count() * 100, 2) as 連対率,
            count(rank <= 3 or null) as ラス回避,
            round(cast(count(rank <= 3 or null) as real) / count() * 100, 2) as ラス回避率,
            -- 座席順位分布
            count(seat = 1 and rank = 1 or null) as '東家-1位',
            count(seat = 1 and rank = 2 or null) as '東家-2位',
            count(seat = 1 and rank = 3 or null) as '東家-3位',
            count(seat = 1 and rank = 4 or null) as '東家-4位',
            round(avg(case when seat = 1 then rank end), 2) as '東家-平均順位',
            sum(case when seat = 1 then gs_count end) as '東家-役満和了',
            count(seat = 1 and rpoint < 0 or null) as '東家-トビ',
            printf("東家：%d+%d+%d+%d=%d (%.2f)",
                count(seat = 1 and rank = 1 or null),
                count(seat = 1 and rank = 2 or null),
                count(seat = 1 and rank = 3 or null),
                count(seat = 1 and rank = 4 or null),
                count(seat = 1 or null),
                round(avg(case when seat = 1 then rank end), 2)
            ) as '東家-順位分布',
            count(seat = 2 and rank = 1 or null) as '南家-1位',
            count(seat = 2 and rank = 2 or null) as '南家-2位',
            count(seat = 2 and rank = 3 or null) as '南家-3位',
            count(seat = 2 and rank = 4 or null) as '南家-4位',
            round(avg(case when seat = 2 then rank end), 2) as '南家-平均順位',
            sum(case when seat = 2 then gs_count end) as '南家-役満和了',
            count(seat = 2 and rpoint < 0 or null) as '南家-トビ',
            printf("南家：%d+%d+%d+%d=%d (%.2f)",
                count(seat = 2 and rank = 1 or null),
                count(seat = 2 and rank = 2 or null),
                count(seat = 2 and rank = 3 or null),
                count(seat = 2 and rank = 4 or null),
                count(seat = 2 or null),
                round(avg(case when seat = 2 then rank end), 2)
            ) as '南家-順位分布',
            count(seat = 3 and rank = 1 or null) as '西家-1位',
            count(seat = 3 and rank = 2 or null) as '西家-2位',
            count(seat = 3 and rank = 3 or null) as '西家-3位',
            count(seat = 3 and rank = 4 or null) as '西家-4位',
            round(avg(case when seat = 3 then rank end), 2) as '西家-平均順位',
            sum(case when seat = 3 then gs_count end) as '西家-役満和了',
            count(seat = 3 and rpoint < 0 or null) as '西家-トビ',
            printf("西家：%d+%d+%d+%d=%d (%.2f)",
                count(seat = 3 and rank = 1 or null),
                count(seat = 3 and rank = 2 or null),
                count(seat = 3 and rank = 3 or null),
                count(seat = 3 and rank = 4 or null),
                count(seat = 3 or null),
                round(avg(case when seat = 3 then rank end), 2)
            ) as '西家-順位分布',
            count(seat = 4 and rank = 1 or null) as '北家-1位',
            count(seat = 4 and rank = 2 or null) as '北家-2位',
            count(seat = 4 and rank = 3 or null) as '北家-3位',
            count(seat = 4 and rank = 4 or null) as '北家-4位',
            round(avg(case when seat = 4 then rank end), 2) as '北家-平均順位',
            sum(case when seat = 4 then gs_count end) as '北家-役満和了',
            count(seat = 4 and rpoint < 0 or null) as '北家-トビ',
            printf("北家：%d+%d+%d+%d=%d (%.2f)",
                count(seat = 4 and rank = 1 or null),
                count(seat = 4 and rank = 2 or null),
                count(seat = 4 and rank = 3 or null),
                count(seat = 4 and rank = 4 or null),
                count(seat = 4 or null),
                round(avg(case when seat = 4 then rank end), 2)
            ) as '北家-順位分布',
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                results.playtime,
                --[individual] --[unregistered_replace] case when guest = 0 then results.name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] results.name, -- ゲスト無効
                --[team] results.name,
                rpoint,
                rank,
                point,
                seat,
                --[individual] results.grandslam,
                ifnull(gs_count, 0) as gs_count
            from
                --[individual] individual_results as results
                --[team] team_results as results
            join game_info on
                game_info.ts == results.ts
            left join grandslam on
                grandslam.thread_ts == results.ts
                --[individual] and grandslam.name == results.name
                --[team] and grandslam.team == results.name
            where
                results.rule_version = :rule_version
                and results.playtime between :starttime and :endtime
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and game_info.same_team = 0
                --[team] and results.name notnull
                --[player_name] and results.name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and game_info.comment like :search_word
            order by
                results.playtime desc
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            sum(point) desc
    """

    return (query_modification(sql))


def details():
    """ゲーム結果の詳細を返すSQLを生成(ゲスト戦も返す)

    Returns:
        str: SQL
    """

    sql = """
        --- game.details()
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
    """

    return (query_modification(sql))


def versus_matrix():
    """直接対戦結果を集計するSQLを生成

    Returns:
        str: SQL
    """

    sql = """
        -- summary.versus_matrix()
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
                --[individual] --[unregistered_replace] case when vs.guest = 0 then vs.name else :guest_name end as vs_name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] vs.name as vs_name, -- ゲスト無効
                --[team] vs.name as vs_name,
                vs.rank as vs_rank,
                vs.rpoint as vs_rpoint,
                vs.point as vs_point
            from
                --[individual] individual_results as my
                --[team] team_results as my
            join game_info on
                game_info.ts == my.ts
            inner join
                --[individual] individual_results as vs on
                --[team] team_results as vs on
                    my.playtime = vs.playtime and my.name != vs.name
            where
                my.rule_version = :rule_version
                and my.playtime between :starttime and :endtime
                and my.name = :player_name
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and vs.guest = 0 -- ゲストなし
                --[friendly_fire] and game_info.same_team = 0
                --[team] and vs.name notnull
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


def total():
    """最終成績集計

    Returns:
        str: SQL
    """

    sql = """
        -- summary.total()
        with point_table as (
            select
                --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] name, -- ゲスト無効
                --[team] name as team,
                --[individual] guest,
                rpoint,
                point,
                ex_point,
                rank
            from
                --[individual] individual_results as results
                --[team] team_results as results
            join game_info on
                game_info.ts == results.ts
            where
                results.rule_version = :rule_version
                and results.playtime between :starttime and :endtime -- 検索範囲
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストアリ(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストナシ
                --[team] --[friendly_fire] and game_info.same_team = 0
                --[team] and team_id notnull -- 未所属除外
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and game_info.comment like :search_word
        ),
        point_summary as (
            select
                --[individual] name,
                --[individual] guest,
                --[team] team,
                count() as count,
                sum(point) as total_point,
                sum(ex_point) as ex_point,
                round(avg(point), 1) as avg_point,
                count(rank = 1 or null) as rank1,
                count(rank = 2 or null) as rank2,
                count(rank = 3 or null) as rank3,
                count(rank = 4 or null) as rank4,
                round(avg(rank), 2) as rank_avg,
                count(rpoint < 0 or null) as flying
            from
                point_table
            group by
                --[individual] name
                --[team] team
        ),
        ranked_points as (
            select
                --[individual] name,
                --[individual] guest,
                --[team] team,
                count,
                total_point,
                ex_point,
                avg_point,
                rank1,
                rank2,
                rank3,
                rank4,
                rank_avg,
                flying,
                rank() over (order by total_point desc) as overall_ranking,
                lag(total_point) over (order by total_point desc) as prev_point,
                first_value(total_point) over (order by total_point desc) as top_point
            from point_summary
        )
        select
            overall_ranking as rank,
            --[individual] case
            --[individual]     when guest = 0 or name = :guest_name then name
            --[individual]     else name || '(<<guest_mark>>)'
            --[individual] end as name,
            --[team] team,
            count,
            round(cast(total_point as real), 1) as total_point,
            ex_point,
            round(cast(avg_point as real), 1) as avg_point,
            rank1,
            rank2,
            rank3,
            rank4,
            rank_avg,
            flying,
            round(cast(rank1 as real)/count*100,2) as rank1_rate,
            round(cast(rank2 as real)/count*100,2) as rank2_rate,
            round(cast(rank3 as real)/count*100,2) as rank3_rate,
            round(cast(rank4 as real)/count*100,2) as rank4_rate,
            round(cast(flying as real)/count*100,2) as flying_rate,
            printf("%d-%d-%d-%d (%.2f)",
                rank1,
                rank2,
                rank3,
                rank4,
                rank_avg
            ) as rank_distr1,
            printf("%d+%d+%d+%d=%d (%.2f)",
                rank1,
                rank2,
                rank3,
                rank4,
                count,
                rank_avg
            ) as rank_distr2,
            case
                when prev_point is null then null
                else abs(round(total_point - prev_point, 1))
            end as diff_from_above,
            case
                when total_point = top_point then null
                else round(top_point - total_point, 1)
            end as diff_from_top
        from ranked_points
        order by rank, count desc;
    """

    return (query_modification(sql))
