#!/usr/bin/env python3
import configparser
import random
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
    target_player = []
    target_team = []

    for pattern, argument in test_conf[sec].items():
        if pattern == "case":
            test_case = argument
            continue

        if pattern == "target_player":
            for x in range(int(argument)):
                target_player.append(random.choice(list(set(g.member_list.values()))))
            continue

        if pattern == "target_team":
            team_list = [x["team"] for x in g.team_list]
            for x in range(int(argument)):
                target_team.append(random.choice(team_list))
            continue

        print("-" * 80)
        print(f"{pattern=} {argument=} {target_player=} {target_team=}")
        g.msg.argument = argument.split() + target_player + target_team

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
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.results.slackpost.main())

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
                pprint(c.results.ranking.main())

            case "report":
                g.msg.argument.append(f"filename:report_{sec}_{pattern}")
                dump(flag)
                pprint(c.report.slackpost.main(), width=200)

            case "pdf":
                g.opt.initialization("report", g.msg.argument)

                g.opt.filename = f"report_{sec}_{pattern}"
                g.prm.update(g.opt)
                dump(flag)
                pprint(c.report.slackpost.results_report.gen_pdf(), width=200)
