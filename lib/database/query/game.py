import global_value as g
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
                --[individual] --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[friendly_fire] and same_team = 0
                --[search_word] and game_info.comment like :search_word
            group by
                individual_results.playtime
            order by
                individual_results.playtime desc
        )
    """

    if not g.opt.individual:  # チーム集計
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
        sql = sql.replace("individual_results", "team_results")

    return (query_modification(sql))


def remark_count(kind):
    """
    メモの内容をカウントするSQLを生成

    Parameters
    ----------
    kind : str
        集計種別
    """

    if kind == "grandslam":
        if g.undefined_word == 0:
            where_string = "and (words.type is null or words.type = 0)"
        else:
            where_string = "and words.type = 0"
    else:
        if g.undefined_word == 2:
            where_string = "and (words.type is null or words.type = 1 or words.type = 2)"
        else:
            where_string = "and (words.type = 1 or words.type = 2)"

    sql = f"""
        -- game.remark_count({kind})
        select
            --[individual] remarks.name,
            --[team] team.name as name,
            matter,
            count() as count,
            type,
            sum(ex_point) as ex_point,
            guest_count,
            same_team
        from
            remarks
        left join member on
            member.name == remarks.name
        left join team on
            member.team_id == team.id
        join game_info on
            game_info.ts == remarks.thread_ts
        left join words on
            words.word == remarks.matter
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[individual] --[player_name] and remarks.name in (<<player_list>>) -- 対象プレイヤー
            --[team] --[player_name] and team.name in (<<player_list>>) -- 対象チーム
            --[friendly_fire] and same_team = 0
            --[search_word] and comment like :search_word
            {where_string}
        group by
            --[individual] remarks.name, matter
            --[team] team.name, matter
    """

    return (query_modification(sql))
