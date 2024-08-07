# テーブル

## result

ポストされたデータを管理するテーブル。*p1* ～ *p4* は東家～北家を表している。

*p?_str* に素点の情報（文字列、記号があるものはそのまま）が記録される。
*p?_str* の式を評価した値は *p?_rpoint* に、素点から計算した獲得ポイントと順位が *p?_point* 、 *p?_rank* に記録される。

ポイント計算などはPython側で処理し、その結果を記録する。リレーションなどはない。

### 内容

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

成績などで表示されるメンバーを管理するテーブル。
便宜上 *id* を主キーとしているが、リレーションはない。
*id=0* はゲストで使用される。

### 内容

| カラム名 | 制約        | 型      | 内容                 |
| -------- | ----------- | ------- | -------------------- |
| id       | PRIMARY KEY | INTEGER |                      |
| name     | NOT NULL    | TEXT    | プレイヤー名         |
| slack_id |             | TEXT    | 未使用               |
| team_id  |             | INTEGER | 所属チームID(未使用) |
| flying   |             | INTEGER | 拡張用フラグ(未使用) |
| reward   |             | INTEGER | 拡張用フラグ(未使用) |
| abuse    |             | INTEGER | 拡張用フラグ(未使用) |

## alias

メンバーの別名を管理するテーブル。
Python側で *{ name: member }* という辞書を生成するのに利用される。
別名ではないメンバー名も *name* に存在する。

### 内容

| カラム名 | 制約        | 型   | 内容               |
| -------- | ----------- | ---- | ------------------ |
| name     | PRIMARY KEY | TEXT | 別名(ニックネーム) |
| member   | NOT NULL    | TEXT | プレイヤー名       |

## team

チーム名を管理するテーブル。内容

| カラム名 | 制約            | 型      | 内容     |
| -------- | --------------- | ------- | -------- |
| id       | PRIMARY KEY     | INTEGER | チームID |
| name     | NOT NULL UNIQUE | TEXT    | チーム名 |

## remarks

ゲーム結果に対して残すメモを記録するテーブル。

### 内容

| カラム名  | 制約     | 型   | 内容                              |
| --------- | -------- | ---- | --------------------------------- |
| thread_ts | NOT NULL | TEXT | 成績結果がslackにポストされた時間 |
| event_ts  | NOT NULL | TEXT | メモがslackにポストされた時間     |
| name      | NOT NULL | TEXT | メモ内容(誰が)                    |
| matter    | NOT NULL | TEXT | メモ内容(何をした)                |

# ビュー

## game_results

横持ちのデータ。
1レコードに1ゲーム分の結果(4人分の成績)を持つ。

### 内容

| カラム名         | 制約 | 内容                         |
| ---------------- | ---- | ---------------------------- |
| playtime         |      | タイムスタンプ(tsを変換)     |
| ts               |      | slackにポストされた時間      |
| p1_name          |      | 東家プレイヤー名             |
| p1_guest         |      | 東家ゲストフラグ(1=ゲスト)   |
| p1_rpoint        |      | 東家素点(計算後)             |
| p1_rank          |      | 東家順位                     |
| p1_point         |      | 東家が獲得したポイント       |
| p2_name          |      | 南家プレイヤー名             |
| p2_guest         |      | 南家ゲストフラグ(1=ゲスト)   |
| p2_rpoint        |      | 南家素点(計算後)             |
| p2_rank          |      | 南家順位                     |
| p2_point         |      | 南家が獲得したポイント       |
| p3_name          |      | 西家プレイヤー名             |
| p3_guest         |      | 西家ゲストフラグ(1=ゲスト)   |
| p3_rpoint        |      | 西家素点(計算後)             |
| p3_rank          |      | 西家順位                     |
| p3_point         |      | 西家が獲得したポイント       |
| p4_name          |      | 北家プレイヤー名             |
| p4_guest         |      | 北家ゲストフラグ(1=ゲスト)   |
| p4_rpoint        |      | 北家素点(計算後)             |
| p4_rank          |      | 北家順位                     |
| p4_point         |      | 北家が獲得したポイント       |
| deposit          |      | 供託                         |
| collection       |      | 集計対象年月(YYYY-MM)        |
| collection_daily |      | 集計対象年月日(YYYY-MM-DD)   |
| rule_version     |      | ルールバージョンを示す文字列 |

## individual_results

縦持ちのデータ。
1レコードに1人分の成績を持つ。

### 内容

| カラム名     | 制約 | 内容                         |
| ------------ | ---- | ---------------------------- |
| playtime     |      | タイムスタンプ(tsを変換)     |
| ts           |      | slackにポストされた時間      |
| seat         |      | 席(1=東、2=南、3=西、4=北)   |
| name         |      | プレイヤー名                 |
| rpoint       |      | 素点(計算後)                 |
| rank         |      | 順位                         |
| point        |      | 獲得ポイント                 |
| guest        |      | ゲストフラグ(1=ゲスト)       |
| collection   |      | 集計対象年月(YYYY-MM)        |
| rule_version |      | ルールバージョンを示す文字列 |

## game_info

### 内容

| カラム名     | 制約 | 内容                                           |
| ------------ | ---- | ---------------------------------------------- |
| ts           |      | slackにポストされた時間                        |
| guest_count  |      | ゲーム内のゲストの人数                         |
| same_team    |      | ゲーム内に同じチームのメンバーが存在すれば `1` |
