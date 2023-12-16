# サンプルSQL

## ゲーム結果
```
SELECT
    datetime(playtime) AS 日時,
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
    name AS プレイヤー名,
    count() AS ゲーム数,
    round(sum(point), 1) AS 累積ポイント,
    round(CAST(sum(point) AS REAL) / CAST(count() AS REAL), 1) AS 平均ポイント,
    count(CASE WHEN rank = 1 THEN 1 END) AS "1位",
    count(CASE WHEN rank = 2 THEN 1 END) AS "2位",
    count(CASE WHEN rank = 3 THEN 1 END) AS "3位",
    count(CASE WHEN rank = 4 THEN 1 END) AS "4位",
    printf("%.2f", round(avg(rank), 2)) AS 平均順位,
    printf("%.2f%", round(CAST(count(CASE WHEN rank = 1 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トップ率,
    printf("%.2f%", round(CAST(count(CASE WHEN rank <= 2 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS 連対率,
    printf("%.2f%", round(CAST(count(CASE WHEN rank <= 3 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス回避率,
    printf("%.2f%", round(CAST(count(CASE WHEN rank = 4 THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス率,
    count(CASE WHEN rpoint < -1  THEN 1 END) AS トビ,
    printf("%.2f%", round(CAST(count(CASE WHEN rpoint < -1  THEN 1 END) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トビ率,
    max(rpoint) AS 最大素点,
    min(rpoint) AS 最小素点,
    round(avg(rpoint), 1) AS 平均素点
FROM
    individual_results
WHERE
    playtime BETWEEN "2023-01-01 12:00:00" AND "2024-01-01 11:59:59" -- 集計期間
GROUP BY
    name
HAVING
    ゲーム数 > (SELECT count() * 0.01 FROM result WHERE playtime BETWEEN "2023-01-01 12:00:00" AND "2024-01-01 11:59:59") -- 規定打数
ORDER BY
    累積ポイント DESC
```

## 月間ランキング

```
SELECT
    collection AS "集計月",
    max(CASE WHEN rank = 1 THEN name END) AS "1位",
    max(CASE WHEN rank = 1 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 1 THEN geme_count END) AS "ゲーム数",
    max(CASE WHEN rank = 2 THEN name END) AS "2位",
    max(CASE WHEN rank = 2 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 2 THEN geme_count END) AS "ゲーム数",
    max(CASE WHEN rank = 3 THEN name END) AS "3位",
    max(CASE WHEN rank = 3 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 3 THEN geme_count END) AS "ゲーム数",
    max(CASE WHEN rank = 4 THEN name END) AS "4位",
    max(CASE WHEN rank = 4 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 4 THEN geme_count END) AS "ゲーム数",
    max(CASE WHEN rank = 5 THEN name END) AS "5位",
    max(CASE WHEN rank = 5 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 5 THEN geme_count END) AS "ゲーム数"
FROM (
    SELECT
        collection,
        rank() OVER (PARTITION BY collection ORDER BY round(sum(point), 1) DESC) AS rank,
        name,
        round(sum(point), 1) AS total,
        count() AS geme_count
    FROM
        individual_results
    GROUP BY
        name, collection
)
GROUP BY
    collection
HAVING
    collection LIKE "2023-%"
```

## 個人成績

```
SELECT
    name AS プレイヤー名, 
    count() AS ゲーム数,
    round(sum(point), 1) AS 累積ポイント,
    round(avg(point), 1) AS 平均ポイント,
    count(CASE WHEN rank = 1 THEN 1 END) AS "1位",
    count(CASE WHEN rank = 2 THEN 1 END) AS "2位",
    count(CASE WHEN rank = 3 THEN 1 END) AS "3位",
    count(CASE WHEN rank = 4 THEN 1 END) AS "4位",
    round(avg(rank), 2) AS 平均順位
FROM
    individual_results
WHERE
    playtime BETWEEN "2023-12-01 12:00:00" AND "2024-01-01 11:59:59"
    AND name = "<Player Name>"
```
全体成績サマリのHAVING句で絞るでも。

## 直近のN回

```
SELECT * FROM (
    SELECT * FROM
        game_results
    WHERE
        "<Player Name>" IN (p1_name, p2_name, p3_name, p4_name)
    ORDER BY
        playtime DESC
    LIMIT 30 -- 直近のゲーム数
)
ORDER BY
    playtime
```