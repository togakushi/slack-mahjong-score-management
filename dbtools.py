#!/usr/bin/env python3
"""
dbtools.py - 補助ツール

help:

usage: dbtools.py [-h] [-c CONFIG] [--service {slack,standard_io,std,web,flask}]
                  [--debug] [--verbose] [--moderate] [--notime]
                  [--compar | --unification [UNIFICATION] | --recalculation | --export [PREFIX] | --import [PREFIX] | --vacuum | --gen-test-data [count]]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        設定ファイル(default: config.ini)
  --service {slack,standard_io,std,web,flask}
                        連携先サービス

logging options:
  --debug               デバッグ情報表示
  --verbose, --trace    詳細デバッグ情報表示
  --moderate            ログレベルがエラー以下のもを非表示
  --notime              ログフォーマットから日時を削除

Required options(amutually exclusive):
  --compar              データ突合
  --unification [UNIFICATION]
                        ファイルの内容に従って記録済みのメンバー名を修正する(default: rename.ini)
  --recalculation       ポイント再計算
  --export [PREFIX]     メンバー設定情報をエクスポート(default prefix: export)
  --import [PREFIX]     メンバー設定情報をインポート(default prefix: export)
  --vacuum              database vacuum
  --gen-test-data [count]
                        テスト用サンプルデータ生成(count=生成回数, default: 1)
"""

import libs.global_value as g
from libs import configuration
from libs.functions import tools as t

if __name__ == "__main__":
    configuration.setup()

    if g.args.compar:
        t.comparison.main()
    if g.args.recalculation:
        t.recalculation.main()
    if g.args.unification:
        t.unification.main()
    if g.args.export_data:
        t.member.export_data()
    if g.args.import_data:
        t.member.import_data()
    if g.args.vacuum:
        t.vacuum.main()
    if g.args.gen_test_data:
        t.gen_test_data.main(g.args.gen_test_data)
