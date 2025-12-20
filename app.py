#!/usr/bin/env python3
"""
app.py - 麻雀のスコアを記録し、集計して表示するツール

help:

    $ ./app.py --help
    usage: app.py [-h] ...

    options:
        -h, --help            show this help message and exit
        -c, --config CONFIG   設定ファイル(default: config.ini)
        -s, --service {slack,discord,standard_io,std,web,flask}
                              連携先サービス

    logging options:
        -d, --debug           デバッグレベル(-d, -dd)
        -v, --verbose         動作ログ出力レベル(-v, -vv, -vvv)
        --moderate            ログレベルがエラー以下のもを非表示
        --notime              ログフォーマットから日時を削除

    Only allowed when --service=standard_io:
        --text TEXT           input text strings

    Only allowed when --service=web:
        --host HOST           listen  address(default: 127.0.0.1)
        --port PORT           bind port(default: 8000)
"""

import sys
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from libs import configuration

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter as discord_adapter
    from integrations.slack.adapter import ServiceAdapter as slack_adapter
    from integrations.standard_io.adapter import ServiceAdapter as std_adapter
    from integrations.web.adapter import ServiceAdapter as web_adapter


if __name__ == "__main__":
    configuration.setup()

    match g.selected_service:
        case "slack":
            import integrations.slack.events.handler as slack

            slack.main(cast("slack_adapter", g.adapter))
        case "discord":
            import integrations.discord.events.handler as discord

            discord.main(cast("discord_adapter", g.adapter))
        case "standard_io":
            import integrations.standard_io.events.handler as standard_io

            standard_io.main(cast("std_adapter", g.adapter))
        case "web":
            import integrations.web.events.handler as webapp

            webapp.main(cast("web_adapter", g.adapter))
        case _:
            sys.exit()
