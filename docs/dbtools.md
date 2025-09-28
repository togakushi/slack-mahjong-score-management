# dbtools

## 概要
データベースファイルをメンテナンスする外部ツール

## 使い方
```Shell
$ uv run ./dbtools.py オプション
```

動作させる固有オプションを1つ指定する。
`config.ini` で定義されいるデータベースファイルが対象となる。

### ヘルプ
```Shell
$ uv run dbtools.py -h
usage: dbtools.py [-h] [-c CONFIG] [--service {slack,standard_io,std,web,flask}] [--debug] [--verbose] [--moderate] [--notime] [--compar | --unification [UNIFICATION] |
                  --recalculation | --export [PREFIX] | --import [PREFIX] | --vacuum | --gen-test-data [count]]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        設定ファイル(default: config.ini)
  --service {slack,standard_io,std,web,flask}
                        連携先サービス
  --compar              データ突合
  --unification [UNIFICATION]
                        ファイルの内容に従って記録済みのメンバー名を修正する(default: rename.ini)
  --recalculation       ポイント再計算
  --export [PREFIX]     メンバー設定情報をエクスポート(default prefix: export)
  --import [PREFIX]     メンバー設定情報をインポート(default prefix: export)
  --vacuum              database vacuum
  --gen-test-data [count]
                        テスト用サンプルデータ生成(count=生成回数, default: 1)

logging options:
  --debug               デバッグ情報表示
  --verbose, --trace    詳細デバッグ情報表示
  --moderate            ログレベルがエラー以下のもを非表示
  --notime              ログフォーマットから日時を削除
  ```

## 固有オプション説明

### --compar
突合処理を実行する。
`--service`で指定されている連携先と接続する。

### --unification [rename.ini]
記録済みデータのゲストプレイヤーの名前を書き換える。

書き換える内容はINIファイルに記述する。
メンバー登録済みの名前や利用不可能文字、登録禁止ワードなどが用いられている名前は書き換えから除外される。

読み込むINIファイルは引数で指定する。省略時は `rename.ini` が使用される。

#### INIファイル書式
```ini
[rename]
置き換え後の名前 = 置き換え前の名前, 置き換え前の名前, ...
```

### --recalculation
記録済みデータの素点からポイントを再計算する。

`config.ini` で定義されている `rule_version` と一致する記録が再計算の対象となる。
過去のデータを含め、すべてのポイントが更新される。

### --export [PREFIX]
メンバー情報をCSVファイルにエクスポートする。
PREFIXの指定を省略した場合は `export` となる。

エクスポートされたCSVファイルの1行目はヘッダ情報であり、インポートの際に必要となる。
ヘッダ情報は以下の通り。

#### メンバーリスト (`export_member.csv`)
```csv
name,slack_id,flying,reward,abuse,team_id
```

ゲストを除いたメンバーのリスト。

`team_id` が空欄のメンバーはどのチームにも所属しない（未所属）。
存在しないチームIDが指定されている場合は未所属扱いとなる。

#### 別名リスト (`export_alias.csv`)
```csv
name,member
```

`name` が別名、`member` がメンバー名（表示される名前）となる。
1行に1組のペアを記述する。

#### 所属チームリスト (`export_team.csv`)
```csv
id,name
```

### --import [PREFIX]
PREFIXから始まるファイル名のCSVファイルからメンバー情報をインポートする。
メンバーリストのみ必須となる。

メンバー情報はデータベースの情報を消去してからインポートされるため、ユーザーIDの欠番はなくなる。

### --vacuum
データベースを最適化する。

### --gen-test-data [count]
動作確認用のテストデータを生成する（[参照](development/test.md)）。

5人編成16チーム前提。総当たり戦。1countあたり455戦。
