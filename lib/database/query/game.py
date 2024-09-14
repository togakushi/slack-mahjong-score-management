from lib.database.common import query_modification


def info():
    """
    ゲーム数のカウント、最初と最後のゲームの時間とコメントを取得するSQLを返す
    """

    sql = """
        -- game.info()
        select
            count() as count,
            --[group_length] substr(first_comment, 1, :group_length) as first_comment,
            --[group_length] substr(last_comment, 1, :group_length) as last_comment,
            --[not_group_length] first_comment, last_comment,
            first_game, last_game
        from (
            select
                first_value(individual_results.playtime) over(order by individual_results.ts asc) as first_game,
                last_value(individual_results.playtime) over(order by individual_results.ts asc) as last_game,
                first_value(game_info.comment) over(order by individual_results.ts asc) as first_comment,
                last_value(game_info.comment) over(order by individual_results.ts asc) as last_comment
            from
                individual_results
            join game_info on
                game_info.ts == individual_results.ts
            where
                individual_results.rule_version = :rule_version
                and individual_results.playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[friendly_fire] and same_team = 0
                --[search_word] and game_info.comment like :search_word
            group by
                individual_results.playtime
            order by
                individual_results.playtime desc
        )
    """

    return (query_modification(sql))


def summary():
    """
    ゲーム結果を集計するSQLを生成
    """

    sql = """
        -- game.summary()
        select
            name,
            count() as count,
            round(sum(point), 1) as pt_total,
            round(avg(point), 1) as pt_avg,
            count(rank = 1 or null) as "1st",
            count(rank = 2 or null) as "2nd",
            count(rank = 3 or null) as "3rd",
            count(rank = 4 or null) as "4th",
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
                --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                --[team] team as name,
                rpoint, rank, point, guest
            from
                individual_results
            join game_info on
                game_info.ts == individual_results.ts
            where
                individual_results.rule_version = :rule_version
                and individual_results.playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[friendly_fire] and same_team = 0
                --[team] and team notnull
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
            individual_results.name as プレイヤー名,
            guest,
            game_info.guest_count,
            seat,
            rpoint,
            rank,
            point,
            grandslam,
            regulations.word as regulation,
            regulations.ex_point,
            regulations.type as type,
            --[not_group_length] game_info.comment
            --[group_length] substr(game_info.comment, 1, :group_length) as comment
        from
            individual_results
        join game_info on
            game_info.ts == individual_results.ts
        left join regulations on
            regulations.thread_ts == individual_results.ts
            and regulations.name == individual_results.name
        where
            individual_results.rule_version = :rule_version
            and individual_results.playtime between :starttime and :endtime
            --[search_word] and game_info.comment like :search_word
        order by
            individual_results.playtime
    """

    return (query_modification(sql))


def remark_count():
    """
    メモの内容をカウントするSQLを生成
    """

    sql = """
        -- game.remark_count()
        select
            name,
            matter,
            count() as count,
            type,
            sum(ex_point) as ex_point,
            guest_count,
            same_team
        from
            remarks
        join game_info on
            game_info.ts == remarks.thread_ts
        left join words on
            words.word == remarks.matter
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
            --[friendly_fire] and same_team = 0
            --[search_word] and comment like :search_word
        group by
            name, matter
    """

    return (query_modification(sql))
