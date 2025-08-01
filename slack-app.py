#!/usr/bin/env python3
# pylint: disable=invalid-name
"""
slack-app.py - Slackに投稿された麻雀のスコアを記録し、集計して表示するツール

help:

    $ ./slack-app.py --help
    usage: slack-app.py [-h] [--service {slack,standard_io,std}] [--debug] [--verbose] [--moderate] [--notime] [-c CONFIG]

    options:
    -h, --help            show this help message and exit
    --service {slack,standard_io,std}
                          連携先サービス
    --debug, --trace      デバッグ情報表示
    --verbose             詳細デバッグ情報表示
    --moderate            ログレベルがエラー以下のもを非表示
    --notime              ログフォーマットから日時を削除
    -c CONFIG, --config CONFIG
                            設定ファイル(default: config.ini)
"""

import sys

import libs.global_value as g
from libs.data import initialization
from libs.functions import configuration

if __name__ == "__main__":
    configuration.setup()
    initialization.initialization_resultdb()
    initialization.read_grade_table()
    configuration.read_memberslist()

    match g.args.service:
        case "slack":
            g.selected_service = "slack"
            import integrations.slack.events.handler as slack
            slack.main()
        case "standard_io" | "std":
            g.selected_service = "standard_io"
            import integrations.standard_io.events.handler as standard_io
            standard_io.main()
        case _:
            sys.exit()
