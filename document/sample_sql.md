# サンプルSQL

```
SELECT
    player as "プレイヤー名",
    count(*) as "ゲーム数",
    round(avg(rank), 2) as "平均順位",
    round(sum(
        CASE
            WHEN rank = 1 THEN round((CAST(rpoint as REAL) - 300) / 10 + 40, 1)
            WHEN rank = 2 THEN round((CAST(rpoint as REAL) - 300) / 10 + 10, 1)
            WHEN rank = 3 THEN round((CAST(rpoint as REAL) - 300) / 10 - 10, 1)
            WHEN rank = 4 THEN round((CAST(rpoint as REAL) - 300) / 10 - 20, 1)
        END
    ), 1) as "獲得ポイント"
FROM gameresults
GROUP BY "プレイヤー名"
ORDER BY "獲得ポイント" DESC;
```
