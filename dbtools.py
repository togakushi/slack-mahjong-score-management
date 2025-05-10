#!/usr/bin/env python3
"""
dbtools.py - 補助ツール

help:

    $ ./dbtools.py --help
    usage: dbtools.py [-h] [--debug] [--verbose] [--moderate] [--notime] [-c CONFIG] [--compar | --unification [UNIFICATION] | --recalculation | --export [PREFIX] | --import [PREFIX] | --vacuum]

    options:
    -h, --help            show this help message and exit
    --debug               デバッグ情報表示
    --verbose             詳細デバッグ情報表示
    --moderate            ログレベルがエラー以下のもを非表示
    --notime              ログフォーマットから日時を削除
    -c CONFIG, --config CONFIG
                            設定ファイル(default: config.ini)
    --compar              データ突合
    --unification [UNIFICATION]
                            ファイルの内容に従って記録済みのメンバー名を修正する(default: rename.ini)
    --recalculation       ポイント再計算
    --export [PREFIX]     メンバー設定情報をエクスポート(default prefix: export)
    --import [PREFIX]     メンバー設定情報をインポート(default prefix: export)
    --vacuum              database vacuum
"""

import libs.global_value as g
from libs.functions import configuration
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
