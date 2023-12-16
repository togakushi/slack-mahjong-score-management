# グラフ生成機能

チャンネル内キーボード「麻雀グラフ」またはスラッシュコマンド「/mahjong graph」で成績グラフを生成する。

引数によって生成するグラフの内容は変化する。

## 引数

有効な引数は以下。無効な引数は無視される。

- 期間指定キーワード
  - 指定なし：「当日」
  - 詳細は [引数の説明](argument_keyword.md) 参照
- 登録名
  - 指定なし：指定期間内に記録のある全員分のポイント推移グラフを出力
  - ひとり：指定者の個人成績グラフを出力
  - ふたり以上：指定されたプレイヤーに絞ってポイント推移グラフを出力

## 全体成績

各プレイヤーの獲得ポイントの推移グラフを出力する。

## 個人成績

対象プレイヤーの以下の成績を出力する。

- ポイントグラフ
  - 獲得ポイント（棒グラフ）
  - 累積ポイント（折れ線グラフ）
- 順位グラフ
  - 獲得順位（折れ線グラフ）
  - 平均順位（折れ線グラフ）