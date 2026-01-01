# ルールセット設定

[settingセクション](mainconf.md#settingセクション)の`rule_config`で設定される。

## 設定内容

|     キー      |        内容        |               型                | 省略時 |  mode=4 省略時   | mode=3 省略時 |                       備考                       |
| ------------- | ------------------ | ------------------------------- | ------ | ---------------- | ------------- | ------------------------------------------------ |
| mode          | 集計モード         | 数値(3 or 4)                    | 4      | ---              | ---           | 四人打ち/三人打ちの指定                          |
| point         | 持ち点             | 数値(100点単位)                 | ---    | 250              | 350           | 配給原点                                         |
| return        | 返し点             | 数値(100点単位)                 | ---    | 300              | 400           | 清算時の基準点(返し点-配給原点x人数がオカとなる) |
| rank_point    | 順位点             | カンマ区切り数値4つ(1000点単位) | ---    | 30, 10, -10, -30 | 30, 0, -30    | 1位から順に並べる(必要以上の列挙は無視される)    |
| ignore_flying | 箱下のカウント表示 | 真偽値                          | ---    | False            | False         | `True` : トビ終了の表示をなくす                  |
| draw_split    | 順位点の山分け     | 真偽値                          | ---    | False            | False         | `True` : 素点同点時に順位点を山分けする          |

セクション名が`rule_version`として登録される。<br />
INIファイルの仕様上、セクション名及びキー名の半角英字はすべて小文字として扱われる。

セクション内のキーが省略された場合はDEFAULTセクションに定義している値がセットされる。<br />
DEFAULTセクションでの定義がない場合は上記表の通りとなる。

<details>
<summary>ルールセットの設定例</summary>

```
[M-league]
mode = 4
origin_point = 250
return_point = 300
rank_point = 30,10,-10,-30
draw_split = True
ignore_flying = True
```

</details>


## マッピング

使用するルールセットと成績登録キーワードの紐付けは[keyword_mappingセクション](mainconf.md#keyword_mappingセクション)で行う。

## 未設定時の動作

### ルールセット定義ファイル

ルールセット定義ファイルの内容が空の場合は追加のルールセットの登録は行われない。

メイン設定内の[mahjongセクション](mainconf.md#mahjongセクション)で設定されたルールが登録される。

### マッピング定義

[keyword_mappingセクション](mainconf.md#keyword_mappingセクション)が未定義の場合、[mahjongセクション](mainconf.md#mahjongセクション)のルールが[settingセクション](mainconf.md#settingセクション)の`keyword`とマッピングされる。

### すべて未定義のデフォルト状態

[mahjongセクション](mainconf.md#mahjongセクション)がすべて未設定の場合、以下のルールセットが定義される。
* ルールバージョン識別子：default_rule
* 集計モード：四人打ち
* 配給原点：25000点
* 返し点：30000点
* 順位点：30 10 -10 -30
* 素点同点時：席順で決定
* トビ表示：アリ

[settingセクション](mainconf.md#settingセクション)の`keyword`が未設定の場合、以下のキーワードがセットされる。
* 終局

[keyword_mappingセクション](mainconf.md#keyword_mappingセクション)が未設定の場合、マッピング設定が空になる。<br />
マッピング設定が空の状態でアプリが起動した場合、[settingセクション](mainconf.md#settingセクション)の`keyword`と[mahjongセクション](mainconf.md#mahjongセクション)の`rule_version`がマッピングされる。
