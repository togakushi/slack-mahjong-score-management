#!/usr/bin/env python3
import configparser
import os
import shutil
from pprint import pprint

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f
from lib.function import configuration


def dump():
    pprint(["*** opt ***", vars(g.opt)])
    pprint(["*** prm ***", vars(g.prm)])
    pprint(["*** game_info ***", d.aggregate.game_info()])


# ---
configuration.setup()
test_conf = configparser.ConfigParser()
test_conf.read(g.args.testcase, encoding="utf-8")

c.member.read_memberslist()

shutil.rmtree(g.cfg.setting.work_dir)
os.mkdir(g.cfg.setting.work_dir)

for sec in test_conf.sections():
    print("=" * 80)
    print(f"[TEST CASE] {sec}")

    for pattern, argument in test_conf[sec].items():
        if pattern == "case":
            test_case = argument
            continue

        print("-" * 80)
        print(f"{pattern=} {argument=}")

        match test_case:
            case "skip":
                pass

            case "config":
                pprint(vars(g.cfg))

            case "help":
                pprint(f.message.help_message())

            case "summary":
                g.opt.initialization("results", argument.split())

                g.prm.update(g.opt)
                dump()
                pprint(c.results.summary.aggregation())

            case "graph":
                g.opt.initialization("graph", argument.split())

                g.opt.filename = f"point_{pattern}"
                g.prm.update(g.opt)
                dump()
                pprint(c.graph.summary.point_plot())

                g.opt.filename = f"rank_{pattern}"
                g.prm.update(g.opt)
                dump()
                pprint(c.graph.summary.rank_plot())

            case "ranking":
                g.msg.argument = argument.split()
                g.prm.update(g.opt)
                dump()
                pprint(c.ranking.slackpost.main())

            case "matrix":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"matrix_{pattern}"
                g.prm.update(g.opt)
                dump()
                pprint(c.report.slackpost.matrix.plot())
