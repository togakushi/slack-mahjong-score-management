def record_count():
    """
    連測連対などの記録をカウントするSQLを生成
    """

    sql = """
        select
            playtime,
            name as "プレイヤー名",
            rank as "順位",
            point as "獲得ポイント",
            rpoint as "最終素点"
        from
            individual_results
        where
            rule_version = :rule_version
            and playtime between :starttime and :endtime
        """

    return(sql)
