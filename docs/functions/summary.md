# 成績サマリ出力

## 構文

チャンネル内呼び出し

```
<呼び出しキーワード> [オプション]
```

スラッシュコマンド

```
/commandname results [オプション]
```

## オプション

### メンバー名/チーム名

指定される人数(チーム数)によって出力内容が切り替わる。

|    指定人数    |         出力内容          |                           備考                            |
| -------------- | ------------------------- | --------------------------------------------------------- |
| 0名            | 全体成績サマリ            |                                                           |
| 1名            | 個人成績/チーム成績サマリ |                                                           |
| 2名以上        | 成績サマリ(比較用)        | 全体成績サマリから指定メンバー/チームだけに絞り込んで表示 |
| 2名以上 + 対戦 | 直接対決サマリ            | 最初に指定されているメンバー/チームが集計対象             |

### 統計
- 座席データ、ベストレコード、ワーストレコードを表示

### 比較 / 点差 / 差分
- ひとつ上の順位のメンバーとの点差を表示
  - 全体成績サマリ/成績サマリ(比較用)でのみ有効

### 戦績
- 戦績データ(ゲーム単位の素点、順位、獲得ポイント)を表示
  - 個人成績サマリ/直接対決サマリでのみ有効

### 詳細
- 戦績データを4人分表示する
  - 戦績の追加オプション（戦績と同時指定した場合のみ有効）
  - 個人成績サマリ/直接対決サマリでのみ有効

### 対戦
- 対戦結果の表示
  - 個人成績サマリでは全員分の勝敗と勝率
  - 成績サマリ(比較用)で指定すると直接対戦サマリを表示する

###  個人 / チーム
- 表示されるサマリ内容を切り替える
  - 個人：個人戦成績
  - チーム：チーム戦成績

### 共通オプション
- [検索範囲指定](argument_keyword.md#検索範囲指定)
- [ゲスト関連](argument_keyword.md#ゲストの成績の取り扱いに関するオプション)

## 全体成績サマリ詳細

メンバー名の指定がない場合、集計期間内で記録されている全メンバーの通算ポイント順に結果を表示する。
ゲスト関連のオプションによって集計内容が変わるため、特記には集計条件が記載される。

全体成績サマリ出力サンプル（通常）

```
【成績サマリ】
    検索範囲：yyyy/mm/dd HH:MM ～ yyyy/mm/dd HH:MM
    最初のゲーム：yyyy/mm/dd HH:MM:SS
    最後のゲーム：yyyy/mm/dd HH:MM:SS
    総ゲーム回数： xxx 回 / トバされた人（延べ）： xx 人
    特記：ゲスト置換なし(※：未登録プレイヤー)

## 名前 : 通算 (平均) / 順位分布 (平均) / トビ ##
ひと     ： +xxx.x (+xx.x) / xx-xx-xx-xx (x.xx) / x
いぬ     ： +xxx.x (+xx.x) / xx-xx-xx-xx (x.xx) / x
さる     ： +xx.x (+x.x) / xx-xx-xx-xx (x.xx) / x
とり     ： ▲xx.x ( ▲x.x) / xx-xx-xx-xx (x.xx) / x
おに(※) ： ▲xxx.x (▲xx.x) / xx-xx-xx-xx (x.xx) / x
```

全体成績サマリ出力サンプル（比較）

```
【成績サマリ】
    検索範囲：yyyy/mm/dd HH:MM ～ yyyy/mm/dd HH:MM
    最初のゲーム：yyyy/mm/dd HH:MM:SS
    最後のゲーム：yyyy/mm/dd HH:MM:SS
    総ゲーム回数： xxx 回 / トバされた人（延べ）： xx 人
    特記：ゲスト置換なし(※：未登録プレイヤー)

## 名前  ： 通算   / 点差 ##
ひと     ： +xxx.x / -----
いぬ     ： +xxx.x /  xx.x
さる     ：  +xx.x /  xx.x
とり     ：  ▲xx.x /  xx.x
おに(※) ： ▲xxx.x /  xx.x
```

## 個人成績サマリ詳細
個人成績サマリ出力サンプル
```
【個人成績】
    プレイヤー名： ひと
    集計範囲：yyyy/mm/dd HH:MM:SS ～ yyyy/mm/dd HH:MM:SS
    対戦数：xxx 戦 (xx 勝 xx 敗 xx 分)
    通算ポイント： +xxx.x
    平均ポイント： +x.x
    平均順位： x.xx
    1位： xx 回 (xx.xx%)
    2位： xx 回 (xx.xx%)
    3位： xx 回 (xx.xx%)
    4位： xx 回 (xx.xx%)
    トビ： xx 回 (x.xx%)
    役満： xx 回 (x.xx%)
    特記：2ゲスト戦の結果を含む

【座席データ】
    # 席：順位分布(平順) / トビ / 役満 #
    東家： xx-xx-xx-xx (x.xx) / x 回 / x 回
    南家： xx-xx-xx-xx (x.xx) / x 回 / x 回
    西家： xx-xx-xx-xx (x.xx) / x 回 / x 回
    北家： xx-xx-xx-xx (x.xx) / x 回 / x 回
```

## 直接対決サマリ詳細
直接対決サマリ出力サンプル
```
【直接対戦結果】
    プレイヤー名： ひと
    対戦相手：さる、いぬ
    検索範囲：yyyy/mm/dd HH:MM ～ yyyy/mm/dd HH:MM
    特記：2ゲスト戦の結果を含む

[ ひと vs さる ]
対戦数： xx 戦 xx 勝 xx 敗
平均素点差： +xxxx点
獲得ポイント合計(自分)： +xxx.xpt
獲得ポイント合計(相手)： ▲xxx.xpt
順位分布(自分)： xx-xx-xx-xx (x.xx)
順位分布(相手)： xx-xx-xx-xx (x.xx)

[ ひと vs いぬ ]
対戦数： xx 戦 xx 勝 xx 敗
平均素点差： +xxxx点
獲得ポイント合計(自分)： +xxx.xpt
獲得ポイント合計(相手)： ▲xxx.xpt
順位分布(自分)： xx-xx-xx-xx (x.xx)
順位分布(相手)： xx-xx-xx-xx (x.xx)
```
