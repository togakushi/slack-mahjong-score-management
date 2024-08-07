# 引数に指定できる共通キーワード

## 検索範囲指定

### 日付指定
- 指定されたキーワードを基にリストに追加
  - キーワードは複数指定可能
  - 実行時の時間を基準に算出
  - リスト内の最小値と最大値の期間を取る

| キーワード                               | 追加される日付                         | 備考               |
| ---------------------------------------- | -------------------------------------- | ------------------ |
| 当日                                     | 12時間前の日付                         |                    |
| 今日                                     | 今日の日付                             |                    |
| 昨日                                     | 昨日の日付                             |                    |
| 今月                                     | 今月月初の日付<br />今月月末の日付     |                    |
| 先月                                     | 先月月初の日付<br />先月月末の日付     |                    |
| 先々月                                   | 先々月月初の日付<br />先々月月末の日付 |                    |
| 今年                                     | 今年の1月1日<br />今年の12月31日       |                    |
| 去年<br />昨年                           | 前年の1月1日<br />前年の12月31日       |                    |
| 一昨年                                   | 前々年の1月1日<br />前々年の12月31日   |                    |
| 最後                                     | 1日後の日付                            |                    |
| 全部                                     | 20200101<br />1日後の日付              | 2020年から翌日まで |
| YYYYMMDD<br />YYYY-MM-DD<br />YYYY/MM/DD | 指定日                                 | MMとDDは常に2桁    |

### 回数指定

| キーワード                 | 内容                                        | 備考 |
| -------------------------- | ------------------------------------------- | ---- |
| 直近NNN                    | NNN回前からのゲームを集計                   | 数字 |
| 規定打数NNN<br />規定数NNN | プレイ数がNNN回以下のメンバーを非表示にする | 数字 |

### 集計単位

| キーワード                 | 内容                                        | 備考 |
| -------------------------- | ------------------------------------------- | ---- |
| daily / デイリー / 日次    | 日単位で合計した通算ポイントを扱う          |      |


## ゲストの成績の取り扱いに関するオプション

### ゲストあり
- 集計結果にゲストの成績を含める
  - 2ゲスト戦の成績は除外される
    - 1ゲームにゲストが2名以上いる場合、ゲストは同名のプレイヤーとして扱われ、成績が合算されてしまう（2ゲスト戦）
    - 正しく集計できないプレイヤーがゲームに存在するため、2ゲスト戦で記録された成績は集計対象外になる（ゲーム自体を無効扱いにする）

### ゲストなし
- 集計結果からゲストの成績を除外する
  - ゲストプレイヤーの成績を集計対象外にする
  - 2ゲスト戦の成績が計上されるようになる（ゲスト以外のプレイヤーの成績は集計可能）

### ゲスト無効
- 未登録メンバーをゲストに置き換えず、個別のメンバーとして集計する
  - ポストされた名前のメンバーとして扱う
  - 敬称は削除される
- ゲストが存在しなくなるため、2ゲスト戦が発生しない
  - すべてのゲームが集計対象になる
