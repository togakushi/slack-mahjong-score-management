#!/usr/bin/env python3
"""
test.py
"""

import configparser
import os
import random
import re
from pprint import pprint

import lib.global_value as g
from lib import command as c
from lib import database as d
from lib import function as f
from lib.function import configuration


def dump(flag: bool = True):
    """パラメータダンプ

    Args:
        flag (bool, optional): 出力フラグ
    """
    if flag:
        pprint(["*** prm ***", g.params], width=200)
        # pprint(["*** game_info ***", d.aggregate.game_info()], width=200)


def test_pattern(flag: bool, test_case: str, sec: str, pattern: str):
    """テストケース実行

    Args:
        flag (bool): ダンプ出力フラグ
        test_case (str): テストケース
        sec (str): 定義セクション
        pattern (str): 実行パターン
    """

    match test_case:
        case "skip":
            pass

        case "member":
            pprint(g.member_list)
            pprint(g.team_list)

        case "help":
            pprint(f.message.help_message(), width=200)

        case "summary":
            g.params = d.common.placeholder(g.cfg.results)
            dump(flag)
            pprint(c.results.slackpost.main())

        case "graph":
            g.params = d.common.placeholder(g.cfg.graph)
            if g.params.get("statistics"):
                g.params.update(filename=f"statistics_{sec}_{pattern}_{g.params["target_player"][0]}")
                dump(flag)
                pprint(c.graph.personal.statistics_plot(), width=200)
            else:
                g.params.update(filename=f"point_{sec}_{pattern}")
                dump(flag)
                pprint(c.graph.summary.point_plot(), width=200)

                g.params.update(filename=f"rank_{sec}_{pattern}")
                dump(flag)
                pprint(c.graph.summary.rank_plot(), width=200)

        case "ranking":
            g.params = d.common.placeholder(g.cfg.ranking)
            dump(flag)
            pprint(c.results.ranking.main())

        case "report":
            g.params = d.common.placeholder(g.cfg.report)
            g.params.update(filename=f"report_{sec}_{pattern}")
            dump(flag)
            pprint(c.report.slackpost.main(), width=200)

        case "pdf":
            g.params = d.common.placeholder(g.cfg.report)
            g.params.update(filename=f"report_{sec}_{pattern}_{g.params["player_name"]}")
            dump(flag)
            pprint(c.report.slackpost.results_report.gen_pdf(), width=200)

        case "rating":
            g.params = d.common.placeholder(g.cfg.results)
            g.params.update(filename=f"rating_{sec}_{pattern}")
            dump(flag)
            pprint(c.graph.rating.plot(), width=200)


def main():
    """メイン処理"""
    g.script_dir = os.path.dirname(os.path.abspath(__file__))
    configuration.setup()
    test_conf = configparser.ConfigParser()
    test_conf.read(g.args.testcase, encoding="utf-8")

    flag = test_conf["default"].getboolean("dump", False)

    d.initialization.initialization_resultdb()
    c.member.read_memberslist()
    always_keyword = ""

    print("=" * 80)
    print(f"config  : {os.path.realpath(os.path.join(g.script_dir, g.args.config))}")
    print(f"database: {g.cfg.db.database_file}")

    for sec in test_conf.sections():
        print("=" * 80)
        print(f"[TEST CASE] {sec}")
        test_case = str()
        all_player = False
        target_player = []
        target_team = []

        for pattern, value in test_conf[sec].items():
            match pattern:
                case s if re.match(r"^case", s):
                    test_case = value
                    continue
                case "target_player":
                    choice_list = list(set(g.member_list.values()))
                    for x in range(int(value)):
                        if not choice_list:
                            break
                        choice_name = random.choice(choice_list)
                        target_player.append(choice_name)
                        choice_list.remove(choice_name)
                    continue
                case "all_player":
                    all_player = True
                    continue
                case "target_team":
                    choice_list = [x["team"] for x in g.team_list]
                    for x in range(int(value)):
                        if not choice_list:
                            break
                        choice_name = random.choice(choice_list)
                        target_team.append(choice_name)
                        choice_list.remove(choice_name)
                    continue
                case "always_keyword":
                    always_keyword = value
                    print("add:", always_keyword)
                    continue

            print("-" * 80)
            argument = f"{value} {always_keyword}"
            if test_conf[sec].getboolean("config", False):
                pprint(["*** config ***", vars(g.cfg)], width=200)

            if all_player:
                for target_player in set(g.member_list.values()):
                    print(f"{pattern=} {argument=} {target_player=} {target_team=} {all_player=}")
                    g.msg.argument = argument.split() + [target_player] + target_team
                    test_pattern(flag, test_case, sec, pattern)
            else:
                print(f"{pattern=} {argument=} {target_player=} {target_team=} {all_player=}")
                g.msg.argument = argument.split() + target_player + target_team
                test_pattern(flag, test_case, sec, pattern)


if __name__ == "__main__":
    main()
