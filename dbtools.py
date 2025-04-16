#!/usr/bin/env python3
"""
dbtools.py
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
