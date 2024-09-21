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
        pprint(["*** opt ***", vars(g.opt)], width=200)
        pprint(["*** prm ***", vars(g.prm)], width=200)
        pprint(["*** game_info ***", d.aggregate.game_info()], width=200)


# ---
configuration.setup()
test_conf = configparser.ConfigParser()
test_conf.read(g.args.testcase, encoding="utf-8")

flag = test_conf["default"].getboolean("dump", False)

d.initialization.initialization_resultdb()
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
        g.msg.argument = argument.split()

        if test_conf[sec].getboolean("config", False):
            pprint(["*** config ***", vars(g.cfg)], width=200)

        match test_case:
            case "skip":
                pass

            case "member":
                pprint(g.member_list)
                pprint(g.team_list)

            case "help":
                pprint(f.message.help_message(), width=200)

            case "summary":
                g.opt.initialization("results", g.msg.argument)

                g.prm.update(g.opt)
                dump(flag)
                pprint(c.results.summary.aggregation(), width=200)

            case "personal":
                g.opt.initialization("results", g.msg.argument)

                g.prm.update(g.opt)
                dump(flag)
                pprint(c.results.personal.aggregation(), width=200)

            case "graph":
                g.opt.initialization("graph", g.msg.argument)

                g.opt.filename = f"point_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.point_plot(), width=200)

                g.opt.filename = f"rank_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.graph.summary.rank_plot(), width=200)

            case "ranking":
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.ranking.slackpost.main(), width=200)

            case "report":
                g.msg.argument.append(f"filename:report_{sec}_{pattern}")
                dump(flag)
                pprint(c.report.slackpost.main(), width=200)

            case "pdf":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"report_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.results.gen_pdf(), width=200)
