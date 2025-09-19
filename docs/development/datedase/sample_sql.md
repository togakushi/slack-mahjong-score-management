# サンプルSQL

## ゲーム結果(月間)
```
SELECT
    datetime(playtime) AS 日時,
    p1_name AS 東家, p1_rpoint * 100 AS 素点, p1_rank AS 順位, p1_point AS ポイント,
    p2_name AS 南家, p2_rpoint * 100 AS 素点, p2_rank AS 順位, p2_point AS ポイント,
    p3_name AS 西家, p3_rpoint * 100 AS 素点, p3_rank AS 順位, p3_point AS ポイント,
    p4_name AS 北家, p4_rpoint * 100 AS 素点, p4_rank AS 順位, p4_point AS ポイント,
    deposit AS 供託
FROM
    game_results
WHERE
    playtime BETWEEN datetime(strftime('%Y-%m-01 12:00:00')) AND datetime(strftime('%Y-%m-01 12:00:00'), '1 month', '-1 second')
```

## 全体成績サマリ(年間)
```
SELECT
    name AS プレイヤー名,
    count() AS ゲーム数,
    round(sum(point), 1) AS 通算ポイント,
    round(avg(point), 1) AS 平均ポイント,
    count(rank = 1 OR NULL) AS "1位",
    count(rank = 2 OR NULL) AS "2位",
    count(rank = 3 OR NULL) AS "3位",
    count(rank = 4 OR NULL) AS "4位",
    printf("%.2f", round(avg(rank), 2)) AS 平均順位,
    printf("%.2f%", round(CAST(count(rank = 1  OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トップ率,
    printf("%.2f%", round(CAST(count(rank <= 2 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS 連対率,
    printf("%.2f%", round(CAST(count(rank <= 3 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス回避率,
    printf("%.2f%", round(CAST(count(rank = 4  OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS ラス率,
    count(rpoint < 0 OR NULL) AS トビ,
    printf("%.2f%", round(CAST(count(rpoint < 0 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2)) AS トビ率,
    max(rpoint) AS 最大素点,
    min(rpoint) AS 最小素点,
    round(avg(rpoint), 1) AS 平均素点
FROM
    individual_results
WHERE
    playtime BETWEEN datetime(strftime('%Y-01-01 12:00:00')) AND datetime(strftime('%Y-12-01 12:00:00'), '1 month', '-1 second') -- 集計期間
GROUP BY
    name
HAVING
    ゲーム数 > (SELECT count() * 0.01 FROM result WHERE playtime BETWEEN datetime(strftime('%Y-01-01 12:00:00')) AND datetime(strftime('%Y-12-01 12:00:00'), '1 month', '-1 second')) -- 規定打数
ORDER BY
    通算ポイント DESC
```

## 月間ランキング
```
SELECT
    collection AS 集計月,
    max(CASE WHEN rank = 1 THEN name END) AS "1位",
    max(CASE WHEN rank = 1 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 1 THEN game_count END) AS "ゲーム数",
    max(CASE WHEN rank = 2 THEN name END) AS "2位",
    max(CASE WHEN rank = 2 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 2 THEN game_count END) AS "ゲーム数",
    max(CASE WHEN rank = 3 THEN name END) AS "3位",
    max(CASE WHEN rank = 3 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 3 THEN game_count END) AS "ゲーム数",
    max(CASE WHEN rank = 4 THEN name END) AS "4位",
    max(CASE WHEN rank = 4 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 4 THEN game_count END) AS "ゲーム数",
    max(CASE WHEN rank = 5 THEN name END) AS "5位",
    max(CASE WHEN rank = 5 THEN total END) AS "ポイント",
    max(CASE WHEN rank = 5 THEN game_count END) AS "ゲーム数"
FROM (
    SELECT
        substr(collection_daily, 1, 7) AS collection,
        rank() OVER (PARTITION BY substr(collection_daily, 1, 7) ORDER BY round(sum(point), 1) DESC) AS rank,
        name,
        round(sum(point), 1) AS total,
        count() AS game_count
    FROM
        individual_results
    GROUP BY
        name, collection_daily
)
GROUP BY
    collection
HAVING
    collection LIKE strftime("%Y-%%")
```

## ゲーム傾向
```
SELECT
    substr(collection_daily, 1, 7) AS 集計月,
    count() / 4 AS ゲーム数,
    round(sum(point), 1) AS 供託,
    count(rpoint < -1 OR NULL) AS "飛んだ人数(延べ)",
    round(CAST(count(rpoint < -1 OR NULL) AS REAL) / CAST(count() / 4 AS REAL) * 100, 2) AS トビ終了率,
    max(rpoint) AS 最大素点,
    min(rpoint) AS 最小素点
FROM
    individual_results
GROUP BY
    substr(collection_daily, 1, 7)
HAVING
    collection_daily LIKE strftime("%Y-%%")
```

## 個人成績
```
SELECT
    substr(collection_daily, 1, 7) AS 集計月,
    count() AS ゲーム数,
    round(sum(point), 1) AS 通算ポイント,
    round(avg(point), 1) AS 平均ポイント,
    count(rank = 1 OR NULL) AS "1位",
    count(rank = 2 OR NULL) AS "2位",
    count(rank = 3 OR NULL) AS "3位",
    count(rank = 4 OR NULL) AS "4位",
    round(avg(rank), 2) AS 平均順位,
    round(CAST(count(rank = 1  OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS トップ率,
    round(CAST(count(rank <= 2 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS 連対率,
    round(CAST(count(rank <= 3 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS ラス回避率,
    round(CAST(count(rank = 4  OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS ラス率,
    count(rpoint < -1 OR NULL) AS トビ,
    round(CAST(count(rpoint < -1 OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS トビ率,
    max(rpoint) AS 最大素点,
    min(rpoint) AS 最小素点,
    round(avg(rpoint), 1) AS 平均素点
FROM
    individual_results
WHERE
    name = "<Player Name>"
GROUP BY
    substr(collection_daily, 1, 7)
HAVING
    collection_daily LIKE strftime("%Y-%%")
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

## 対戦結果（対個人）
```
SELECT
    my.name AS プレイヤー,
    vs.name AS 対戦相手,
    printf("%3d戦 %3d勝 %3d敗",
        count(),
        count(my.rank < vs.rank OR NULL),
        count(my.rank > vs.rank OR NULL)
    ) AS 対戦結果,
    round(CAST(count(my.rank < vs.rank OR NULL) AS REAL) / CAST(count() AS REAL) * 100, 2) AS 勝率
FROM
    individual_results my
INNER JOIN
    individual_results vs
        ON (my.playtime = vs.playtime AND my.name != vs.name)
GROUP BY
    my.name, vs.name
HAVING
    my.name = "<Player Name>"
ORDER BY
    count() DESC
```

## ゲーム毎の通算ポイント(移動合計)、平均ポイント（移動平均）
```
SELECT
    count() OVER moving AS count,
    playtime,
    rank,
    point,
    round(sum(point) OVER moving, 1) AS point_sum,
    round(avg(point) OVER moving, 1) AS point_avg,
    round(avg(rank) OVER moving, 2) AS rank_avg
FROM
    individual_results
WHERE
    name = "<Player Name>"
WINDOW
    moving AS (PARTITION BY name ORDER BY playtime)
```
