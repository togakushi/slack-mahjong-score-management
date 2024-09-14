from lib.database.common import query_modification


def gamedata():
    """
    ゲーム結果集計(チーム戦)
    """

    sql = """
        -- team.gamedata()
        select
            --[not_collection] --[not_group_by] count() over moving as count,
            --[not_collection] --[group_by] sum(count) over moving as count,
            --[collection] sum(count) over moving as count,
            --[not_collection] replace(playtime, "-", "/") as playtime,
            --[collection] replace(collection, "-", "/") as playtime,
            team,
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
                team,
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
                --[friendly_fire] and same_team = 0
                --[search_word] and game_info.comment like :search_word
            --[not_collection] --[group_by] group by -- コメント集約
            --[not_collection] --[group_by]     --[not_comment] collection_daily, team
            --[not_collection] --[group_by]     --[comment] game_info.comment, team
            --[not_collection] --[group_by]     --[group_length] substr(game_info.comment, 1, :group_length), team
            --[collection] group by
            --[collection_daily]     collection_daily, team  -- 日次集計
            --[collection_monthly]     substr(collection_daily, 1, 7), team -- 月次集計
            --[collection_yearly]     substr(collection_daily, 1, 4), team -- 年次集計
            order by
                --[not_collection] individual_results.playtime desc
                --[collection_daily] collection_daily desc
                --[collection_monthly] substr(collection_daily, 1, 7) desc
                --[collection_yearly] substr(collection_daily, 1, 4) desc
        )
        window
            --[not_collection] moving as (partition by team order by playtime)
            --[collection] moving as (partition by name order by collection)
        order by
            --[not_collection] playtime, team
            --[collection] collection, team
    """

    return (query_modification(sql))


def total():
    """
    チーム集計結果を返すSQLを生成
    """

    sql = """
        -- team.total()
        select
            team,
            round(sum(point),1) as pt_total,
            printf("%d-%d-%d-%d (%.2f)",
                count(rank = 1 or null),
                count(rank = 2 or null),
                count(rank = 3 or null),
                count(rank = 4 or null),
                round(avg(rank), 2)
            ) as rank_distr,
            count() as count
        from
            individual_results
        join game_info
            on individual_results.ts = game_info.ts
        where
            individual_results.rule_version = :rule_version
            and individual_results.playtime between :starttime and :endtime
            and team not null
            --[friendly_fire] and same_team = 0
            --[search_word] and game_info.comment like :search_word
        group by
            team
        order by
            pt_total desc
    """

    return (query_modification(sql))
