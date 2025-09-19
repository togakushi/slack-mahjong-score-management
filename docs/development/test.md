# テストデータ生成

## ツール起動
- 基本設定
- 空DB生成

## サンプルメンバーインポート

```shell
$ ./dbtools.py --import ./tests/test_data/saki
```

- 1チーム5人編成
- 16チーム

## データ生成

```shell
$ ./dbtools.py --gen-test-data
```

- 16チーム総当たり戦
  - 2275戦/チーム
  - 455戦/人
