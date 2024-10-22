# テーブル

## result

ポストされたデータを管理するテーブル。*p1* ～ *p4* は東家～北家を表している。

*p?_str* に素点の情報（文字列、記号があるものはそのまま）が記録される。<br />
*p?_str* の式を評価した値は *p?_rpoint* に、素点から計算した獲得ポイントと順位が *p?_point* 、 *p?_rank* に記録される。

ポイント計算などはPython側で処理し、その結果を記録する。リレーションなどはない。

### 内容

|   カラム名   |    制約     |    型     |              内容              |
| ------------ | ----------- | --------- | ------------------------------ |
| ts           | PRIMARY KEY | TEXT      | slackにポストされた時間        |
| playtime     | UNIQUE      | TIMESTAMP | タイムスタンプ(tsを変換)       |
| p1_name      | NOT NULL    | TEXT      | 東家プレイヤー名               |
| p1_str       | NOT NULL    | TEXT      | slackに入力された東家の素点    |
| p1_rpoint    |             | INTEGER   | 東家素点(計算後)               |
| p1_rank      |             | INTEGER   | 東家順位                       |
| p1_point     |             | INTEGER   | 東家が獲得したポイント         |
| p2_name      | NOT NULL    | TEXT      | 南家プレイヤー名               |
| p2_str       | NOT NULL    | TEXT      | slackに入力された南家の素点    |
| p2_rpoint    |             | INTEGER   | 南家素点(計算後)               |
| p2_rank      |             | INTEGER   | 南家順位                       |
| p2_point     |             | INTEGER   | 南家が獲得したポイント         |
| p3_name      | NOT NULL    | TEXT      | 西家プレイヤー名               |
| p3_str       | NOT NULL    | TEXT      | slackに入力された西家の素点    |
| p3_rpoint    |             | INTEGER   | 西家素点(計算後)               |
| p3_rank      |             | INTEGER   | 西家順位                       |
| p3_point     |             | INTEGER   | 西家が獲得したポイント         |
| p4_name      | NOT NULL    | TEXT      | 北家プレイヤー名               |
| p4_str       | NOT NULL    | TEXT      | slackに入力された北家の素点    |
| p4_rpoint    |             | INTEGER   | 北家素点(計算後)               |
| p4_rank      |             | INTEGER   | 北家順位                       |
| p4_point     |             | INTEGER   | 北家が獲得したポイント         |
| deposit      |             | INTEGER   | 供託(配給原点と素点合計の差分) |
| rule_version |             | TEXT      | ルールバージョンを示す文字列   |
| comment      |             | TEXT      | ゲームコメント                 |

## member

成績などで表示されるメンバーを管理するテーブル。<br />
便宜上 *id* を主キーとしているが、リレーションはない。<br />
*id=0* はゲストで使用される。

### 内容

| カラム名 |    制約     |   型    |         内容         |
| -------- | ----------- | ------- | -------------------- |
| id       | PRIMARY KEY | INTEGER |                      |
| name     | NOT NULL    | TEXT    | プレイヤー名         |
| slack_id |             | TEXT    | 未使用               |
| team_id  |             | INTEGER | 所属チームID         |
| flying   |             | INTEGER | 拡張用フラグ(未使用) |
| reward   |             | INTEGER | 拡張用フラグ(未使用) |
| abuse    |             | INTEGER | 拡張用フラグ(未使用) |

## alias

メンバーの別名を管理するテーブル。<br />
Python側で *{ name: member }* という辞書を生成するのに利用される。<br />
別名ではないメンバー名も *name* に存在する。

### 内容

| カラム名 |    制約     |  型  |        内容        |
| -------- | ----------- | ---- | ------------------ |
| name     | PRIMARY KEY | TEXT | 別名(ニックネーム) |
| member   | NOT NULL    | TEXT | プレイヤー名       |

## team

チーム名を管理するテーブル。

### 内容

| カラム名 |      制約       |   型    |   内容   |
| -------- | --------------- | ------- | -------- |
| id       | PRIMARY KEY     | INTEGER | チームID |
| name     | NOT NULL UNIQUE | TEXT    | チーム名 |

## remarks

ゲーム結果に対して残すメモを記録するテーブル。

### 内容

| カラム名  |   制約   |  型  |               内容                |
| --------- | -------- | ---- | --------------------------------- |
| thread_ts | NOT NULL | TEXT | 成績結果がslackにポストされた時間 |
| event_ts  | NOT NULL | TEXT | メモがslackにポストされた時間     |
| name      | NOT NULL | TEXT | メモ内容(誰が)                    |
| matter    | NOT NULL | TEXT | メモ内容(何をした)                |

## words

 `remarks` に記録された単語の種別。祝儀や卓外ペナルティなど、ポイントに影響がある単語を登録。

 単語の定義は設定ファイル内の[regulationsセクション](../setting/customize.md#regulationsセクション)で行う。

### 内容

| カラム名 |      制約       |   型    |                   内容                   |
| -------- | --------------- | ------- | ---------------------------------------- |
| word     | NOT NULL UNIQUE | TEXT    | `remarks` で使用される単語               |
| type     |                 | INTEGER | 種別(別表)                               |
| ex_point |                 | INTEGER | 卓外ポイントとして追加計算されるポイント |

#### typeの種別

| type |           内容           |               備考                |
| ---- | ------------------------ | --------------------------------- |
| null | 未定義                   | regulationsセクションの設定に従う |
| 0    | 役満扱い                 |                                   |
| 1    | 卓外ポイント(個人清算)   |                                   |
| 2    | ワードのカウントのみ     |                                   |
| 3    | 卓外ポイント(チーム清算) | 未実装                            |


# ビュー

## game_results

個人戦結果の横持ちデータ。<br />
1レコードに1ゲーム分の結果(4人分の成績)を持つ。

### 内容

|     カラム名     |       参照元        |             内容             |
| ---------------- | ------------------- | ---------------------------- |
| playtime         |                     | タイムスタンプ(tsを変換)     |
| ts               | result.ts           | slackにポストされた時間      |
| p1_name          | result.p1_name      | 東家プレイヤー名             |
| p1_team          | team.name           | 東家所属チーム名             |
| p1_guest         |                     | 東家ゲストフラグ(`1`=ゲスト) |
| p1_rpoint        | result.p1_rpoint    | 東家素点(計算後)             |
| p1_rank          | result.p1_rank      | 東家順位                     |
| p1_point         | result.p1_point     | 東家が獲得したポイント       |
| p2_name          | result.p2_name      | 南家プレイヤー名             |
| p2_team          | team.name           | 南家所属チーム名             |
| p2_guest         |                     | 南家ゲストフラグ(`1`=ゲスト) |
| p2_rpoint        | result.p2_rpoint    | 南家素点(計算後)             |
| p2_rank          | result.p2_rank      | 南家順位                     |
| p2_point         | result.p3_point     | 南家が獲得したポイント       |
| p3_name          | result.p3_name      | 西家プレイヤー名             |
| p3_team          | team.name           | 西家所属チーム名             |
| p3_guest         |                     | 西家ゲストフラグ(`1`=ゲスト) |
| p3_rpoint        | result.p3_rpoint    | 西家素点(計算後)             |
| p3_rank          | result.p3_rank      | 西家順位                     |
| p3_point         | result.p3_point     | 西家が獲得したポイント       |
| p4_name          | result.p4_name      | 北家プレイヤー名             |
| p4_team          | team.name           | 北家所属チーム名             |
| p4_guest         |                     | 北家ゲストフラグ(`1`=ゲスト) |
| p4_rpoint        | result.p4_rpoint    | 北家素点(計算後)             |
| p4_rank          | result.p4_rank      | 北家順位                     |
| p4_point         | result.p4_point     | 北家が獲得したポイント       |
| deposit          |                     | 供託                         |
| collection_daily |                     | 集計対象年月日(YYYY-MM-DD)   |
| comment          | result.comment      | コメント                     |
| guest_count      |                     | ゲーム内のゲストの合計人数   |
| same_team        |                     | `1`=チーム同卓あり           |
| rule_version     | result.rule_version | ルールバージョンを示す文字列 |

## individual_results

個人戦結果の縦持ちデータ。<br />
1レコードに1人分の成績を持つ。

### 内容

|     カラム名     |        参照元        |                内容                |
| ---------------- | -------------------- | ---------------------------------- |
| playtime         |                      | タイムスタンプ(tsを変換)           |
| ts               | result.ts            | slackにポストされた時間            |
| seat             |                      | 席(`1`=東、`2`=南、`3`=西、`4`=北) |
| name             | result.p?_name       | プレイヤー名                       |
| rpoint           | result.p?_rpoint     | 素点(計算後)                       |
| rank             | result.p?_rank       | 順位                               |
| point            | result.p?_point      | 獲得ポイント(卓外ポイント込み)     |
| grandslam        |                      | 和了した役満( `remarks` から取得)  |
| ex_point         | regulations.ex_point | 卓外ポイント                       |
| guest            |                      | ゲストフラグ(`1`=ゲスト)           |
| collection_daily |                      | 集計対象年月日(YYYY-MM-DD)         |
| rule_version     | result.rule_version  | ルールバージョンを示す文字列       |
| comment          | result.comment       | ゲームコメント                     |

## team_results

チーム戦結果の縦持ちデータ。<br />
1レコードに1人分の成績を持つ。

|     カラム名     |        参照元        |                内容                |
| ---------------- | -------------------- | ---------------------------------- |
| playtime         |                      | タイムスタンプ(tsを変換)           |
| ts               | result.ts            | slackにポストされた時間            |
| seat             |                      | 席(`1`=東、`2`=南、`3`=西、`4`=北) |
| name             |                      | チーム名                           |
| rpoint           | result.p?_rpoint     | 素点(計算後)                       |
| rank             | result.p?_rank       | 順位                               |
| point            | result.p?_point      | 獲得ポイント(卓外ポイント込み)     |
| ex_point         | regulations.ex_point | 卓外ポイント                       |
| collection_daily |                      | 集計対象年月日(YYYY-MM-DD)         |
| rule_version     | result.rule_version  | ルールバージョンを示す文字列       |
| comment          | result.comment       | ゲームコメント                     |

## game_info

### 内容

|   カラム名   |       参照元        |                      内容                      |
| ------------ | ------------------- | ---------------------------------------------- |
| playtime     |                     | タイムスタンプ(tsを変換)                       |
| ts           | result.ts           | slackにポストされた時間                        |
| guest_count  |                     | ゲーム内のゲストの人数                         |
| same_team    |                     | ゲーム内に同じチームのメンバーが存在すれば `1` |
| rule_version | result.rule_version | ルールバージョンを示す文字列                   |
| comment      | result.comment      | ゲームコメント                                 |

## grandslam

`remarks` から役満に関するレコードだけを抽出したもの。

### 内容

| カラム名  |      参照元       |                         内容                         |
| --------- | ----------------- | ---------------------------------------------------- |
| thread_ts | remarks.thread_ts | 対象のゲームのタイムスタンプ                         |
| name      | remarks.name      | 記録対象プレイヤー名                                 |
| team      | team.name         | 記録対象チーム名                                     |
| grandslam | remarks.matter    | 内容(複数レコードある場合はカンマ区切りで連結される) |
| gs_count  |                   | 1ゲーム内での発生回数                                |

## regulations

`remarks` から卓外ポイントに関するレコードだけを抽出したもの。

### 内容

| カラム名  |      参照元       |                         内容                         |
| --------- | ----------------- | ---------------------------------------------------- |
| thread_ts | remarks.thread_ts | 対象のゲームのタイムスタンプ                         |
| name      | remarks.name      | 記録対象プレイヤー名                                 |
| team      | team.name         | 記録対象チーム名                                     |
| word      | remarks.matter    | 内容(複数レコードある場合はカンマ区切りで連結される) |
| ex_point  | words.ex_point    | 追加計算されるポイント合計(卓外ポイント)             |
