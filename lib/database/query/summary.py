import global_value as g
from lib.database.common import query_modification


def gamedata():
    """
    通算ポイント推移/平均順位推移
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
                individual_results.playtime,
                --[collection_daily] collection_daily as collection,
                --[collection_monthly] substr(collection_daily, 1, 7) as collection,
                --[collection_yearly] substr(collection_daily, 1, 4) as collection,
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
                individual_results
            join
                game_info on individual_results.ts = game_info.ts
            where
                individual_results.rule_version = :rule_version
                and individual_results.playtime between :starttime and :endtime
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and same_team = 0
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
            order by
                --[not_collection] individual_results.playtime desc
                --[collection_daily] collection_daily desc
                --[collection_monthly] substr(collection_daily, 1, 7) desc
                --[collection_yearly] substr(collection_daily, 1, 4) desc
        )
        window
            --[not_collection] moving as (partition by name order by playtime)
            --[collection] moving as (partition by name order by collection)
        order by
            --[not_collection] playtime, name
            --[collection] collection, name
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))


def total():
    """
    最終成績集計
    """

    sql = """
        -- summary.total()
        select
            --[team] name as team,
            --[individual] name,
            count() as count,
            round(sum(point), 1) as pt_total,
            round(avg(point), 1) as pt_avg,
            abs(round(sum(point) - lag(sum(point)) over (order by sum(point) desc), 1)) as pt_diff,
            count(rank = 1 or null) as "1st",
            count(rank = 2 or null) as "2nd",
            count(rank = 3 or null) as "3rd",
            count(rank = 4 or null) as "4th",
            round(avg(rank), 2) as rank_avg,
            printf("%d-%d-%d-%d (%.2f)",
                count(rank = 1 or null),
                count(rank = 2 or null),
                count(rank = 3 or null),
                count(rank = 4 or null),
                round(avg(rank), 2)
            ) as rank_distr,
            count(rpoint < 0 or null) as flying
        from (
            select
                --[individual] --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] name, -- ゲスト無効
                --[team] name,
                --[individual] guest,
                rpoint, rank, point
            from
                individual_results
            join game_info on
                game_info.ts == individual_results.ts
            where
                individual_results.rule_version = :rule_version
                and individual_results.playtime between :starttime and :endtime -- 検索範囲
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[individual] --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and same_team = 0
                --[team] and name notnull
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and game_info.comment like :search_word
            order by
                individual_results.playtime desc
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            pt_total desc
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))


def results():
    """
    成績集計
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
            printf("東家： %d-%d-%d-%d (%.2f)",
                count(seat = 1 and rank = 1 or null),
                count(seat = 1 and rank = 2 or null),
                count(seat = 1 and rank = 3 or null),
                count(seat = 1 and rank = 4 or null),
                round(avg(case when seat = 1 then rank end), 2)
            ) as '東家-順位分布',
            count(seat = 2 and rank = 1 or null) as '南家-1位',
            count(seat = 2 and rank = 2 or null) as '南家-2位',
            count(seat = 2 and rank = 3 or null) as '南家-3位',
            count(seat = 2 and rank = 4 or null) as '南家-4位',
            round(avg(case when seat = 2 then rank end), 2) as '南家-平均順位',
            sum(case when seat = 2 then gs_count end) as '南家-役満和了',
            count(seat = 2 and rpoint < 0 or null) as '南家-トビ',
            printf("南家： %d-%d-%d-%d (%.2f)",
                count(seat = 2 and rank = 1 or null),
                count(seat = 2 and rank = 2 or null),
                count(seat = 2 and rank = 3 or null),
                count(seat = 2 and rank = 4 or null),
                round(avg(case when seat = 2 then rank end), 2)
            ) as '南家-順位分布',
            count(seat = 3 and rank = 1 or null) as '西家-1位',
            count(seat = 3 and rank = 2 or null) as '西家-2位',
            count(seat = 3 and rank = 3 or null) as '西家-3位',
            count(seat = 3 and rank = 4 or null) as '西家-4位',
            round(avg(case when seat = 3 then rank end), 2) as '西家-平均順位',
            sum(case when seat = 3 then gs_count end) as '西家-役満和了',
            count(seat = 3 and rpoint < 0 or null) as '西家-トビ',
            printf("西家： %d-%d-%d-%d (%.2f)",
                count(seat = 3 and rank = 1 or null),
                count(seat = 3 and rank = 2 or null),
                count(seat = 3 and rank = 3 or null),
                count(seat = 3 and rank = 4 or null),
                round(avg(case when seat = 3 then rank end), 2)
            ) as '西家-順位分布',
            count(seat = 4 and rank = 1 or null) as '北家-1位',
            count(seat = 4 and rank = 2 or null) as '北家-2位',
            count(seat = 4 and rank = 3 or null) as '北家-3位',
            count(seat = 4 and rank = 4 or null) as '北家-4位',
            round(avg(case when seat = 4 then rank end), 2) as '北家-平均順位',
            sum(case when seat = 4 then gs_count end) as '北家-役満和了',
            count(seat = 4 and rpoint < 0 or null) as '北家-トビ',
            printf("北家： %d-%d-%d-%d (%.2f)",
                count(seat = 4 and rank = 1 or null),
                count(seat = 4 and rank = 2 or null),
                count(seat = 4 and rank = 3 or null),
                count(seat = 4 and rank = 4 or null),
                round(avg(case when seat = 4 then rank end), 2)
            ) as '北家-順位分布',
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                individual_results.playtime,
                --[individual] --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
                --[individual] --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                --[team] individual_results.name,
                rpoint,
                rank,
                point,
                seat,
                --[individual] individual_results.grandslam,
                ifnull(gs_count, 0) as gs_count
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


def details():
    """
    ゲーム結果の詳細を返すSQLを生成(ゲスト戦も返す)
    """

    sql = """
        --- game.details()
        select
            --[not_search_word] individual_results.playtime,
            --[search_word] game_info.comment as playtime,
            --[team] team_results.name as name,
            --[individual] individual_results.name as name,
            --[individual] guest,
            --[individual] game_info.guest_count,
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
            individual_results
        join game_info on
            game_info.ts == individual_results.ts
        left join grandslam on
            grandslam.thread_ts == individual_results.ts
            --[individual] and grandslam.name == individual_results.name
            --[team] and grandslam.team == team_results.name
        left join regulations on
            regulations.thread_ts == individual_results.ts
            --[individual] and regulations.name == individual_results.name
            --[team] and regulations.team == team_results.name
        where
            individual_results.rule_version = :rule_version
            and individual_results.playtime between :starttime and :endtime
            --[search_word] and game_info.comment like :search_word
        order by
            individual_results.playtime
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))


def versus_matrix():
    """
    直接対戦結果を集計するSQLを生成
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
                individual_results my
            join game_info on
                game_info.ts == my.ts
            inner join
                individual_results vs on
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

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))
