# テーブル

## result

| カラム名     | 制約        | 型        | 内容                                  |
| ------------ | ----------- | --------- | ------------------------------------- |
| ts           | PRIMARY KEY | TEXT      | slackにポストされた時間               |
| playtime     | UNIQUE      | TIMESTAMP | タイムスタンプ(tsを変換)              |
| p1_name      | NOT NULL    | TEXT      | 東家プレイヤー名                      |
| p1_str       | NOT NULL    | TEXT      | slackに入力された東家の素点           |
| p1_rpoint    |             | INTEGER   | 東家素点(計算後)                      |
| p1_rank      |             | INTEGER   | 東家順位                              |
| p1_point     |             | INTEGER   | 東家が獲得したポイント                |
| p2_name      | NOT NULL    | TEXT      | 南家プレイヤー名                      |
| p2_str       | NOT NULL    | TEXT      | slackに入力された南家の素点           |
| p2_rpoint    |             | INTEGER   | 南家素点(計算後)                      |
| p2_rank      |             | INTEGER   | 南家順位                              |
| p2_point     |             | INTEGER   | 南家が獲得したポイント                |
| p3_name      | NOT NULL    | TEXT      | 西家プレイヤー名                      |
| p3_str       | NOT NULL    | TEXT      | slackに入力された西家の素点           |
| p3_rpoint    |             | INTEGER   | 西家素点(計算後)                      |
| p3_rank      |             | INTEGER   | 西家順位                              |
| p3_point     |             | INTEGER   | 西家が獲得したポイント                |
| p4_name      | NOT NULL    | TEXT      | 北家プレイヤー名                      |
| p4_str       | NOT NULL    | TEXT      | slackに入力された北家の素点           |
| p4_rpoint    |             | INTEGER   | 北家素点(計算後)                      |
| p4_rank      |             | INTEGER   | 北家順位                              |
| p4_point     |             | INTEGER   | 北家が獲得したポイント                |
| deposit      |             | INTEGER   | 供託                                  |
| rule_version |             | TEXT      | ルールバージョンを示す文字列          |
| comment      |             | TEXT      | コメント入力欄(入力できるI/Fは未実装) |

## member

| カラム名 | 制約        | 型      | 内容                 |
| -------- | ----------- | ------- | -------------------- |
| id       | PRIMARY KEY | INTEGER |                      |
| name     | NOT NULL    | TEXT    | プレイヤー名         |
| slack_id |             | TEXT    | 未使用               |
| flying   |             | INTEGER | 拡張用フラグ(未使用) |
| reward   |             | INTEGER | 拡張用フラグ(未使用) |
| abuse    |             | INTEGER | 拡張用フラグ(未使用) |

## alias

| カラム名 | 制約        | 型   | 内容               |
| -------- | ----------- | ---- | ------------------ |
| name     | PRIMARY KEY | TEXT | 別名(ニックネーム) |
| member   | NOT NULL    | TEXT | プレイヤー名       |

# ビュー

## game_results

| カラム名     | 制約 | 内容                         |
| ------------ | ---- | ---------------------------- |
| playtime     |      | タイムスタンプ               |
| p1_name      |      | 東家プレイヤー名             |
| p1_guest     |      | 東家ゲストフラグ(1=ゲスト)   |
| p1_rpoint    |      | 東家素点(計算後)             |
| p1_rank      |      | 東家順位                     |
| p1_point     |      | 東家が獲得したポイント       |
| p2_name      |      | 南家プレイヤー名             |
| p2_guest     |      | 南家ゲストフラグ(1=ゲスト)   |
| p2_rpoint    |      | 南家素点(計算後)             |
| p2_rank      |      | 南家順位                     |
| p2_point     |      | 南家が獲得したポイント       |
| p3_name      |      | 西家プレイヤー名             |
| p3_guest     |      | 西家ゲストフラグ(1=ゲスト)   |
| p3_rpoint    |      | 西家素点(計算後)             |
| p3_rank      |      | 西家順位                     |
| p3_point     |      | 西家が獲得したポイント       |
| p4_name      |      | 北家プレイヤー名             |
| p4_guest     |      | 北家ゲストフラグ(1=ゲスト)   |
| p4_rpoint    |      | 北家素点(計算後)             |
| p4_rank      |      | 北家順位                     |
| p4_point     |      | 北家が獲得したポイント       |
| deposit      |      | 供託                         |
| collection   |      | 集計対象年月(YYYY-MM)        |
| rule_version |      | ルールバージョンを示す文字列 |

## individual_results

| カラム名     | 制約 | 内容                         |
| ------------ | ---- | ---------------------------- |
| playtime     |      | タイムスタンプ               |
| seat         |      | 席(1=東、2=南、3=西、4=北)   |
| name         |      | プレイヤー名                 |
| rpoint       |      | 素点(計算後)                 |
| rank         |      | 順位                         |
| point        |      | 獲得ポイント                 |
| guest        |      | ゲストフラグ(1=ゲスト)       |
| collection   |      | 集計対象年月(YYYY-MM)        |
| rule_version |      | ルールバージョンを示す文字列 |
