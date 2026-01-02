# ルールセット設定例
## ルールセット設定
以下を*rule.ini*に定義する。
```
[麻雀部ルール]
rank_point = 20, 10, -10, -20

[M-league]
mode = 4
origin_point = 250
return_point = 300
rank_point = 30, 10, -10, -30
draw_split = True
ignore_flying = True

[サンマルール]
mode = 3
rank_point = 20, 0, -20
```

## メイン設定パターン別のルールセット登録状況の説明
> [!TIP]
> ルールセット以外の設定状況については他の設定事例を参照

### rule_configのみ定義
```
[mahjong]

[setting]
rule_config = rule.ini
```

#### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'終局': 'default_rule'}
[INFO][rule:info] 麻雀部ルール: mode=4, origin_point=250, return_point=300, rank_point=[20, 10, -10, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] M-league: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, -30], draw_split=True, ignore_flying=True
[INFO][rule:info] サンマルール: mode=3, origin_point=350, return_point=400, rank_point=[20, 0, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] default_rule: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, 30], draw_split=False, ignore_flying=False
```
* mahjongセクションで基本ルールセットの設定がすべて省略されているため、`default_rule`として基本ルールセットが定義される
* settingセクションの`keyword`が省略されているため、デフォルト値の「終局」が`keyword`にセットされる
* keyword_mappingセクションがなくマッピングが作成されないため、「終局」と`default_rule`がマッピングされる

### keywordを定義
```
[mahjong]

[setting]
keyword = 成績記録
rule_config = rule.ini
```

#### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'成績記録': 'default_rule'}
[INFO][rule:info] 麻雀部ルール: mode=4, origin_point=250, return_point=300, rank_point=[20, 10, -10, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] M-league: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, -30], draw_split=True, ignore_flying=True
[INFO][rule:info] サンマルール: mode=3, origin_point=350, return_point=400, rank_point=[20, 0, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] default_rule: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, 30], draw_split=False, ignore_flying=False
```
* mahjongセクションで基本ルールセットの設定がすべて省略されているため、`default_rule`として基本ルールセットが定義される
* keyword_mappingセクションがなくマッピングが作成されないため、「成績記録」と`default_rule`がマッピングされる

### 基本ルールセットを定義
```
[mahjong]
rule_version = 基本ルール

[setting]
keyword = 成績記録
rule_config = rule.ini
```

#### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'成績記録': '基本ルール'}
[INFO][rule:info] 麻雀部ルール: mode=4, origin_point=250, return_point=300, rank_point=[20, 10, -10, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] M-league: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, -30], draw_split=True, ignore_flying=True
[INFO][rule:info] サンマルール: mode=3, origin_point=350, return_point=400, rank_point=[20, 0, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] 基本ルール: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, 30], draw_split=False, ignore_flying=False
```
* ルールバージョン識別子「基本ルール」が基本ルールセットとして登録される
* keyword_mappingセクションがなくマッピングが作成されないため、「成績記録」と`基本ルール`がマッピングされる

### マッピングを定義
```
[mahjong]
rule_version = 基本ルール

[setting]
keyword = 成績記録
rule_config = rule.ini

[keyword_mapping]
えむるーる = M-league
三麻成績記録 = サンマルール
部活動 = 麻雀部ルール
練習試合 =
```

#### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'えむるーる': 'M-league', '三麻成績記録': 'サンマルール', '部活動': '麻雀部ルール', '練習試合': '基本ルール'}
[INFO][rule:info] 麻雀部ルール: mode=4, origin_point=250, return_point=300, rank_point=[20, 10, -10, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] M-league: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, -30], draw_split=True, ignore_flying=True
[INFO][rule:info] サンマルール: mode=3, origin_point=350, return_point=400, rank_point=[20, 0, -20], draw_split=False, ignore_flying=False
[INFO][rule:info] 基本ルール: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, 30], draw_split=False, ignore_flying=False
```
* マッピングが定義されるため、`keyword`指定の成績登録キーワードとmahjongセクションの基本ルールセットのマッピングは行われない
  * マッピング定義が空のときのみ自動定義処理が動く
  * 基本ルールセットとのマッピングはルールバージョン識別子を省略する、もしくは`rule_version`を明記する
* `keyword`指定の成績登録キーワードを使いたい場合は、keyword_mappingセクションで改めて定義する
  * マッピングがある場合、`keyword`の指定は意味を持たなくなるため省略しても問題ない
    * デフォルト値の「終局」がセットされた状態で処理が進むが、マッピングされなければ使われることはない
