#!/usr/bin/env python3
"""
app.py - 麻雀のスコアを記録し、集計して表示するツール

help:

    $ ./app.py --help
    usage: app.py [-h] ...
"""

import sys
from typing import cast

import libs.global_value as g
from integrations import factory
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
            slack.main(cast(factory.slack.adapter.AdapterInterface, g.adapter))
        case "standard_io":
            import integrations.standard_io.events.handler as standard_io
            standard_io.main(cast(factory.standard_io.adapter.AdapterInterface, g.adapter))
        case "web":
            import integrations.web.events.handler as webapp
            webapp.main(cast(factory.web.adapter.AdapterInterface, g.adapter))
        case _:
            sys.exit()
