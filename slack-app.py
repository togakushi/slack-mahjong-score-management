#!/usr/bin/env python3
# pylint: disable=invalid-name
"""
slack-app.py - Slackに投稿された麻雀のスコアを記録し、集計して表示するツール

help:

    $ ./slack-app.py --help
    usage: slack-app.py [-h] ...
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

    match g.selected_service:
        case "slack":
            import integrations.slack.events.handler as slack
            slack.main()
        case "standard_io":
            import integrations.standard_io.events.handler as standard_io
            standard_io.main()
        case "web":
            import integrations.web.events.handler as webapp
            webapp.main()
        case _:
            sys.exit()
