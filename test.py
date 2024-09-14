#!/usr/bin/env python3
import configparser
from pprint import pprint

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f
from lib.function import configuration


def dump(flag=True):
    if flag:
        pprint(["*** opt ***", vars(g.opt)])
        pprint(["*** prm ***", vars(g.prm)])
        pprint(["*** game_info ***", d.aggregate.game_info()])


# ---
configuration.setup()
test_conf = configparser.ConfigParser()
test_conf.read(g.args.testcase, encoding="utf-8")

flag = test_conf["default"].getboolean("dump", False)
c.member.read_memberslist()

for sec in test_conf.sections():
    print("=" * 80)
    print(f"[TEST CASE] {sec}")
    test_case = None

    for pattern, argument in test_conf[sec].items():
        if pattern == "case":
            test_case = argument
            continue

        print("-" * 80)
        print(f"{pattern=} {argument=}")

        if test_conf[sec].getboolean("config", False):
            pprint(["*** config ***", vars(g.cfg)])

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
                dump(flag)
                pprint(c.results.summary.aggregation())

            case "personal":
                g.opt.initialization("results", argument.split())

                g.prm.update(g.opt)
                dump(flag)
                pprint(c.results.personal.aggregation())

            case "team":
                g.opt.initialization("results", argument.split())

                g.prm.update(g.opt)
                dump(flag)
                pprint(c.results.team.aggregation())

            case "graph":
                g.opt.initialization("graph", argument.split())

                g.opt.filename = f"point_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.point_plot())

                g.opt.filename = f"rank_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.rank_plot())

            case "team-graph":
                g.opt.initialization("graph", argument.split())
                g.opt.team_total = True

                g.opt.filename = f"point_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.point_plot())

                g.opt.filename = f"rank_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.rank_plot())

            case "ranking":
                g.msg.argument = argument.split()
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.ranking.slackpost.main())

            case "matrix":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"matrix_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.matrix.plot())

            case "report":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"report_monthly_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.monthly.plot())

                g.opt.filename = f"report_winner_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.winner.plot())

                g.opt.filename = f"report_personal_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.personal.plot())

            case "pdf":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"report_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.results.gen_pdf())
