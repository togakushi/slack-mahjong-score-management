# slack-mahjong-score-management

## 概要

slackに投稿された麻雀のスコアを記録、集計するツール。
四人打ち専用。

- [セットアップ方法](docs/setting/setup.md)

## 主な機能

### スコア記録（[詳細](docs/functions/score_record.md)）

以下のフォーマットに一致した投稿をデータベースに取り込む。
```
<指定キーワード>
東家プレイヤー名 東家素点
南家プレイヤー名 南家素点
西家プレイヤー名 西家素点
北家プレイヤー名 北家素点
```

### メンバー管理（[詳細](docs/functions/member_management.md)）
成績管理をするプレイヤーを登録し、スコアを蓄積する。

### 成績サマリ出力機能（[詳細](docs/functions/summary.md)）
記録されているスコアを集計し、一覧で出力する。

### グラフ生成機能（[詳細](docs/functions/graph.md)）
記録されているスコアを集計し、グラフで出力する。

### ランキング出力機能（[詳細](docs/functions/ranking.md)）
記録されているスコアを集計し、ランキング形式で出力する。

### レポート出力機能（[詳細](docs/functions/report.md)）
月間成績上位者、個人成績一覧、ゲーム統計情報を表形式で出力する。

### スラッシュコマンド（[使い方](docs/functions/command.md)）
出力結果をボットから直接DMで受け取る。
