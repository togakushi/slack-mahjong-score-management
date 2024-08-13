import re
import textwrap

from lib.function import global_value as g


def _query_modification(sql: str):
    """
    オプションの内容でクエリを修正する
    """

    # ゲスト関連フラグ
    if g.opt.unregistered_replace:
        sql = sql.replace("--[unregistered_replace] ", "")
        if g.opt.guest_skip:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")

    # チーム戦
    if not g.opt.friendly_fire:
        sql = sql.replace("--[friendly_fire] ", "")

    # 日次集計
    if g.opt.daily:
        sql = sql.replace("--[daily] ", "")
    else:
        sql = sql.replace("--[not_daily] ", "")
    if g.prm.search_word or g.prm.group_length:
        sql = sql.replace("--[group_by] ", "")
    else:
        sql = sql.replace("--[not_group_by] ", "")

    # コメント検索
    if g.opt.search_word:
        sql = sql.replace("--[search_word] ", "")

    if g.opt.group_length:
        sql = sql.replace("--[group_length] ", "")
    else:
        sql = sql.replace("--[not_group_length] ", "")
        if g.prm.search_word:
            sql = sql.replace("--[comment] ", "")
        else:
            sql = sql.replace("--[not_comment] ", "")

    # 直近N検索用（全範囲取得してから絞る）
    if g.prm.target_count != 0:
        sql = sql.replace(
            "and my.playtime between",
            "-- and my.playtime between"
        )

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    return (sql)


def game_info():
    """
    ゲーム数のカウント、最初と最後のゲームの時間とコメントを取得するSQLを返す
    """

    sql = """
        select
            count() as count,
            --[group_length] substr(first_comment, 1, :group_length) as first_comment,
            --[group_length] substr(last_comment, 1, :group_length) as last_comment,
            --[not_group_length] first_comment, last_comment,
            first_game, last_game
        from (
            select
                first_value(playtime) over(order by ts asc) as first_game,
                last_value(playtime) over(order by ts asc) as last_game,
                first_value(comment) over(order by ts asc) as first_comment,
                last_value(comment) over(order by ts asc) as last_comment
            from
                individual_results
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and comment like :search_word
            group by
                playtime
            order by
                playtime desc
        )
    """

    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def record_count():
    """
    連測連対などの記録をカウントするSQLを生成
    """

    sql = """
        select
            playtime,
            --[unregistered_replace] case when guest = 0 then name else :guest_name end as "プレイヤー名", -- ゲスト有効
            --[unregistered_not_replace] name as "プレイヤー名", -- ゲスト無効
            rank as "順位",
            point as "獲得ポイント",
            rpoint as "最終素点"
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
            --[guest_skip] and guest = 0 -- ゲストなし
            --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
            --[search_word] and comment like :search_word
    """

    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def game_results():
    """
    ゲーム結果を集計するSQLを生成
    """

    sql = """
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
            round(avg(rank), 2) as rank_avg,
            count(rpoint < 0 or null) as flying
        from (
            select
                --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                rpoint, rank, point, guest, rule_version
            from
                individual_results
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and comment like :search_word
            order by
                playtime desc
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            pt_total desc
    """

    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def personal_results():
    """
    個人成績を集計するSQLを生成
    """

    sql = """
        select
            name as プレイヤー名,
            count() as ゲーム数,
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
                playtime,
                --[unregistered_replace] case when guest = 0 then individual_results.name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                rpoint,
                rank,
                point,
                seat,
                individual_results.grandslam,
                ifnull(gs_count, 0) as gs_count
            from
                individual_results
            join game_info on
                game_info.ts == individual_results.ts
            left join grandslam on
                grandslam.thread_ts == individual_results.ts
                and grandslam.name == individual_results.name
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime
                --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and individual_results.name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and comment like :search_word
            order by
                playtime desc
        )
        group by
            name
        having
            count() >= :stipulated -- 規定打数
        order by
            sum(point) desc
    """

    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def game_details():
    """
    ゲーム結果の詳細を返すSQLを生成(ゲスト戦も返す)
    """

    sql = """
        select
            playtime,
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
            --[not_group_length] comment
            --[group_length] substr(comment, 1, :group_length) as comment
        from
            individual_results
        join game_info on
            game_info.ts == individual_results.ts
        left join regulations on
            regulations.thread_ts == individual_results.ts
            and regulations.name == individual_results.name
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            --[search_word] and comment like :search_word
        order by
            playtime
    """

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def versus_matrix():
    """
    直接対戦結果を集計するSQLを生成
    """

    sql = """
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

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def personal_gamedata():
    """
    ゲーム結果集計(個人戦)
    """

    sql = """
        -- ゲーム結果集計(個人戦)
        select
            --[not_daily] --[not_group_by] count() over moving as count,
            --[not_daily] --[group_by] sum(count) over moving as count,
            --[daily] sum(count) over moving as count,
            --[not_daily] replace(playtime, "-", "/") as playtime,
            --[daily] replace(collection_daily, "-", "/") as playtime,
            name,
            rank,
            point,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(point) over moving, 1) as point_avg,
            round(avg(rank) over moving, 2) as rank_avg,
            comment
        from (
            select
                --[daily] count() as count,
                --[not_daily] --[group_by] count() as count,
                playtime,
                collection_daily,
                --[unregistered_replace] case when guest = 0 then name else :guest_name end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                --[not_daily] rank,
                --[daily] round(avg(rank), 2) as rank,
                --[not_daily] --[not_group_by] point,
                --[not_daily] --[group_by] round(sum(point), 1) as point,
                --[daily] round(sum(point), 1) as point,
                game_info.guest_count,
                --[not_group_length] comment
                --[group_length] substr(comment, 1, :group_length) as comment
            from
                individual_results
            join
                game_info on individual_results.ts = game_info.ts
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime
                --[guest_not_skip] and game_info.guest_count <= 1 -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
                --[player_name] and name in (<<player_list>>) -- 対象プレイヤー
                --[search_word] and comment like :search_word
            --[not_daily] --[group_by] group by -- コメント集約
            --[not_daily] --[group_by]     --[not_comment] collection_daily, name
            --[not_daily] --[group_by]     --[comment] comment, name
            --[not_daily] --[group_by]     --[group_length] substr(comment, 1, :group_length), name
            --[daily] group by -- 日次集計
            --[daily]     collection_daily, name
            order by
                --[not_daily] playtime desc
                --[daily] collection_daily desc
        )
        window
            --[not_daily] moving as (partition by name order by playtime)
            --[daily] moving as (partition by name order by collection_daily)
        order by
            --[not_daily] playtime, name
            --[daily] collection_daily, name
    """

    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def team_gamedata():
    """
    ゲーム結果集計(チーム戦)
    """

    sql = """
        -- ゲーム結果集計(チーム戦)
        select
            --[not_daily] --[not_group_by] count() over moving as count,
            --[not_daily] --[group_by] sum(count) over moving as count,
            --[daily] sum(count) over moving as count,
            --[not_daily] replace(playtime, "-", "/") as playtime,
            --[daily] replace(collection_daily, "-", "/") as playtime,
            team,
            rank,
            point,
            round(sum(point) over moving, 1) as point_sum,
            round(avg(point) over moving, 1) as point_avg,
            round(avg(rank) over moving, 2) as rank_avg,
            comment
        from (
            select
                --[daily] count() as count,
                --[not_daily] --[group_by] count() as count,
                playtime,
                collection_daily,
                team,
                --[not_daily] rank,
                --[daily] round(avg(rank), 2) as rank,
                --[not_daily] --[not_group_by] point,
                --[not_daily] --[group_by] round(sum(point), 1) as point,
                --[daily] round(sum(point), 1) as point,
                game_info.guest_count,
                --[not_group_length] comment
                --[group_length] substr(comment, 1, :group_length) as comment
            from
                individual_results
            join
                game_info on individual_results.ts = game_info.ts
            where
                rule_version = :rule_version
                and playtime between :starttime and :endtime
                --[search_word] and comment like :search_word
            --[not_daily] --[group_by] group by -- コメント集約
            --[not_daily] --[group_by]     --[not_comment] collection_daily, team
            --[not_daily] --[group_by]     --[comment] comment, team
            --[not_daily] --[group_by]     --[group_length] substr(comment, 1, :group_length), team
            --[daily] group by -- 日次集計
            --[daily]     collection_daily, team
            order by
                --[not_daily] playtime desc
                --[daily] collection_daily desc
        )
        window
            --[not_daily] moving as (partition by team order by playtime)
            --[daily] moving as (partition by team order by collection_daily)
        order by
            --[not_daily] playtime, team
            --[daily] collection_daily, team
    """

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def monthly_report():
    """
    """

    sql = """
        select
            collection as 集計月,
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
            collection
        order by
            collection desc
    """

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def winner_report():
    """
    """

    sql = """
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
                    collection,
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

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)


def team_total():
    """
    チーム集計結果を返すSQLを生成
    """

    sql = """
        select
            team,
            round(sum(point),1) as total,
            round(avg(rank),2) as rank,
            count() as count
        from
            individual_results
        join game_info
            on individual_results.ts = game_info.ts
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
            and team not null
            --[friendly_fire] and same_team = 0
            --[search_word] and comment like :search_word
        group by
            team
        order by
            total desc
    """

    sql = _query_modification(sql)
    g.logging.trace(f"sql: {textwrap.dedent(sql)}")  # type: ignore
    g.logging.trace(f"prm: {g.prm.to_dict()}")  # type: ignore

    return (sql)
