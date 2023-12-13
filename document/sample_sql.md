# サンプルSQL

## ゲーム結果
```
SELECT
    playtime,
    p1_name AS 東家, p1_rpoint * 100 AS 素点, p1_rank AS 順位, p1_point AS ポイント,
    p2_name AS 南家, p2_rpoint * 100 AS 素点, p2_rank AS 順位, p2_point AS ポイント,
    p3_name AS 西家, p3_rpoint * 100 AS 素点, p3_rank AS 順位, p3_point AS ポイント,
    p4_name AS 北家, p4_rpoint * 100 AS 素点, p4_rank AS 順位, p4_point AS ポイント,
    deposit AS 供託
FROM
    result
WHERE
    playtime BETWEEN "2023-12-01 12:00:00" AND "2024-01-01 11:59:59"
ORDER BY
    playtime DESC
```

## 全体成績サマリ

```
SELECT
    プレイヤー名,
    count() AS ゲーム数,
    round(sum(ポイント), 1) AS 累積ポイント,
    round(CAST(sum(ポイント) AS REAL) / CAST(count() AS REAL), 1) AS 平均ポイント,
    count(CASE WHEN 順位 = 1 THEN 1 END) AS "1位",
    count(CASE WHEN 順位 = 2 THEN 1 END) AS "2位",
    count(CASE WHEN 順位 = 3 THEN 1 END) AS "3位",
    count(CASE WHEN 順位 = 4 THEN 1 END) AS "4位",
    printf("%.2f", round(avg(順位), 2)) AS 平均順位,
    count(CASE WHEN 素点 < -1  THEN 1 END) AS トビ,
    printf("%.2f%", round(CAST(count(CASE WHEN 素点 < -1  THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トビ率,
    printf("%.2f%", round(CAST(count(CASE WHEN 順位 = 1 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トップ率,
    printf("%.2f%", round(CAST(count(CASE WHEN 順位 <= 2 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS 連対率,
    printf("%.2f%", round(CAST(count(CASE WHEN 順位 <= 3 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス回避率,
    printf("%.2f%", round(CAST(count(CASE WHEN 順位 = 4 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス率,
    max(素点) AS 最大素点,
    min(素点) AS 最小素点,
    round(avg(素点), 1) AS 平均素点
FROM (
    SELECT
        playtime,
        p1_name AS プレイヤー名,
        p1_rpoint AS 素点,
        p1_rank AS 順位,
        p1_point AS ポイント
    FROM
        result
    UNION SELECT playtime, p2_name, p2_rpoint, p2_rank, p2_point FROM result
    UNION SELECT playtime, p3_name, p3_rpoint, p3_rank, p3_point FROM result
    UNION SELECT playtime, p4_name, p4_rpoint, p4_rank, p4_point FROM result
)
WHERE
    playtime BETWEEN "2023-01-01 12:00:00" AND "2024-01-01 11:59:59" -- 集計期間
GROUP BY
    プレイヤー名
HAVING
    ゲーム数 > (SELECT count() * 0.01 FROM result WHERE playtime BETWEEN "2023-01-01 12:00:00" AND "2024-01-01 11:59:59") -- 規定打数
ORDER BY
    累積ポイント DESC
```

## 月間ランキング

```
SELECT
    集計月,
    max(CASE WHEN 順位 = 1 THEN プレイヤー名 END) AS "1位",
    max(CASE WHEN 順位 = 1 THEN 累積ポイント END) AS "ポイント",
    max(CASE WHEN 順位 = 1 THEN ゲーム数 END) AS "ゲーム数",
    max(CASE WHEN 順位 = 2 THEN プレイヤー名 END) AS "2位",
    max(CASE WHEN 順位 = 2 THEN 累積ポイント END) AS "ポイント",
    max(CASE WHEN 順位 = 2 THEN ゲーム数 END) AS "ゲーム数",
    max(CASE WHEN 順位 = 3 THEN プレイヤー名 END) AS "3位",
    max(CASE WHEN 順位 = 3 THEN 累積ポイント END) AS "ポイント",
    max(CASE WHEN 順位 = 3 THEN ゲーム数 END) AS "ゲーム数",
    max(CASE WHEN 順位 = 4 THEN プレイヤー名 END) AS "4位",
    max(CASE WHEN 順位 = 4 THEN 累積ポイント END) AS "ポイント",
    max(CASE WHEN 順位 = 4 THEN ゲーム数 END) AS "ゲーム数",
    max(CASE WHEN 順位 = 5 THEN プレイヤー名 END) AS "5位",
    max(CASE WHEN 順位 = 5 THEN 累積ポイント END) AS "ポイント",
    max(CASE WHEN 順位 = 5 THEN ゲーム数 END) AS "ゲーム数"
FROM (
    SELECT
        集計月,
        rank() OVER (PARTITION BY 集計月 ORDER BY 累積ポイント DESC) AS 順位,
        プレイヤー名,
        累積ポイント,
        ゲーム数
    FROM (
        SELECT
            プレイヤー名,
            round(sum(ポイント), 1) AS 累積ポイント,
            round(CAST(sum(ポイント) AS REAL) / CAST(count() AS REAL), 1) AS 平均ポイント,
            round(avg(順位), 2) AS 平均順位,
            count() AS ゲーム数,
            CASE
                WHEN playtime BETWEEN "2023-01-01 12:00:00" AND "2023-02-01 11:59:59" THEN "2023年01月"
                WHEN playtime BETWEEN "2023-02-01 12:00:00" AND "2023-03-01 11:59:59" THEN "2023年02月"
                WHEN playtime BETWEEN "2023-03-01 12:00:00" AND "2023-04-01 11:59:59" THEN "2023年03月"
                WHEN playtime BETWEEN "2023-04-01 12:00:00" AND "2023-05-01 11:59:59" THEN "2023年04月"
                WHEN playtime BETWEEN "2023-05-01 12:00:00" AND "2023-06-01 11:59:59" THEN "2023年05月"
                WHEN playtime BETWEEN "2023-06-01 12:00:00" AND "2023-07-01 11:59:59" THEN "2023年06月"
                WHEN playtime BETWEEN "2023-07-01 12:00:00" AND "2023-08-01 11:59:59" THEN "2023年07月"
                WHEN playtime BETWEEN "2023-08-01 12:00:00" AND "2023-09-01 11:59:59" THEN "2023年08月"
                WHEN playtime BETWEEN "2023-09-01 12:00:00" AND "2023-10-01 11:59:59" THEN "2023年09月"
                WHEN playtime BETWEEN "2023-10-01 12:00:00" AND "2023-11-01 11:59:59" THEN "2023年10月"
                WHEN playtime BETWEEN "2023-11-01 12:00:00" AND "2023-12-01 11:59:59" THEN "2023年11月"
                WHEN playtime BETWEEN "2023-12-01 12:00:00" AND "2024-01-01 11:59:59" THEN "2023年12月"
            END AS 集計月
        FROM (
            SELECT
                playtime,
                p1_name AS プレイヤー名,
                p1_rpoint AS 素点,
                p1_rank AS 順位,
                p1_point AS ポイント
            FROM
                result
            UNION SELECT playtime, p2_name, p2_rpoint, p2_rank, p2_point FROM result
            UNION SELECT playtime, p3_name, p3_rpoint, p3_rank, p3_point FROM result
            UNION SELECT playtime, p4_name, p4_rpoint, p4_rank, p4_point FROM result
        )
        GROUP BY
            プレイヤー名, 集計月
        HAVING
            NOT 集計月 ISNULL
    )
)
GROUP BY
    集計月
```

## 個人成績

```
SELECT
    "<Player Name>" AS プレイヤー名, 
    count() AS ゲーム数,
    sum(
        CASE
            WHEN p1_name = "<Player Name>" THEN p1_point
            WHEN p2_name = "<Player Name>" THEN p2_point
            WHEN p3_name = "<Player Name>" THEN p3_point
            WHEN p4_name = "<Player Name>" THEN p4_point
        END
    ) AS 累積ポイント,
    round(
        avg(
            CASE
                WHEN p1_name = "<Player Name>" THEN p1_point
                WHEN p2_name = "<Player Name>" THEN p2_point
                WHEN p3_name = "<Player Name>" THEN p3_point
                WHEN p4_name = "<Player Name>" THEN p4_point
            END
        ), 1
    ) AS 平均ポイント,
    count(
        CASE
            WHEN p1_name = "<Player Name>" AND p1_rank = 1 THEN 1
            WHEN p2_name = "<Player Name>" AND p2_rank = 1 THEN 1
            WHEN p3_name = "<Player Name>" AND p3_rank = 1 THEN 1
            WHEN p4_name = "<Player Name>" AND p4_rank = 1 THEN 1
        END
    ) AS "1位",
    count(
        CASE
            WHEN p1_name = "<Player Name>" AND p1_rank = 2 THEN 1
            WHEN p2_name = "<Player Name>" AND p2_rank = 2 THEN 1
            WHEN p3_name = "<Player Name>" AND p3_rank = 2 THEN 1
            WHEN p4_name = "<Player Name>" AND p4_rank = 2 THEN 1
        END
    ) AS "2位",
    count(
        CASE
            WHEN p1_name = "<Player Name>" AND p1_rank = 3 THEN 1
            WHEN p2_name = "<Player Name>" AND p2_rank = 3 THEN 1
            WHEN p3_name = "<Player Name>" AND p3_rank = 3 THEN 1
            WHEN p4_name = "<Player Name>" AND p4_rank = 3 THEN 1
        END
    ) AS "3位",
    count(
        CASE
            WHEN p1_name = "<Player Name>" AND p1_rank = 4 THEN 1
            WHEN p2_name = "<Player Name>" AND p2_rank = 4 THEN 1
            WHEN p3_name = "<Player Name>" AND p3_rank = 4 THEN 1
            WHEN p4_name = "<Player Name>" AND p4_rank = 4 THEN 1
        END
    ) AS "4位",
    round(
        avg(
            CASE
                WHEN p1_name = "<Player Name>" THEN p1_rank
                WHEN p2_name = "<Player Name>" THEN p2_rank
                WHEN p3_name = "<Player Name>" THEN p3_rank
                WHEN p4_name = "<Player Name>" THEN p4_rank 
            END
        ), 2
    ) AS 平均順位
FROM
    result
WHERE
    playtime BETWEEN "2023-12-01 12:00:00" AND "2024-01-01 11:59:59"
    AND "<Player Name>" IN (p1_name, p2_name, p3_name, p4_name)
```
全体成績サマリのHAVING句で絞る方がラク
