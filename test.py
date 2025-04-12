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


def test_pattern(flag: dict, test_case: str, sec: str, pattern: str):
    """テストケース実行

    Args:
        flag (dict): フラグ格納辞書
        test_case (str): テストケース
        sec (str): 定義セクション
        pattern (str): 実行パターン
    """

    def graph_point():
        """ポイント推移グラフ"""
        if len(g.params["player_list"]) == 1:
            pprint([
                "exec: lib.graph.personal.plot()",
                c.graph.personal.plot(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)
        else:
            pprint([
                "exec: lib.graph.summary.point_plot()",
                c.graph.summary.point_plot(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

    def graph_rank():
        """順位推移グラフ"""
        pprint([
            "exec: lib.graph.summary.rank_plot()",
            c.graph.summary.rank_plot(),
            f"{g.params=}" if flag.get("dump") else "g.params={...}",
        ], width=120)

    def graph_statistics():
        """統計グラフ"""
        pprint([
            "exec: lib.graph.personal.statistics_plot()",
            c.graph.personal.statistics_plot(),
            f"{g.params=}" if flag.get("dump") else "g.params={...}",
        ], width=120)

    # 追加オプション
    pre_params = f.common.analysis_argument(g.msg.argument)
    if flag.get("save") and not pre_params.get("filename"):
        g.msg.argument.append(f"filename:{flag.get("filename", "dummy")}")

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
            if flag.get("save"):
                g.params.update(filename=flag.get("filename", "dummy"))
            pprint([
                "exec: lib.results.slackpost.main()",
                c.results.slackpost.main(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

        case "graph":
            g.params = d.common.placeholder(g.cfg.graph)
            if g.params.get("filename"):
                save_filename = g.params["filename"]
                g.params.update(filename=f"{save_filename}_point")
                graph_point()
                g.params.update(filename=f"{save_filename}_rank")
                graph_rank()
                if g.params.get("statistics"):
                    g.params.update(filename=f"{save_filename}")
                    graph_statistics()
            else:
                g.params.update(filename=f"point_{sec}_{pattern}")
                graph_point()
                g.params.update(filename=f"rank_{sec}_{pattern}")
                graph_rank()
                if g.params.get("statistics"):
                    g.params.update(filename=f"statistics_{sec}_{pattern}")
                    graph_statistics()

        case "graph_point":
            g.params = d.common.placeholder(g.cfg.graph)
            graph_point()

        case "graph_rank":
            g.params = d.common.placeholder(g.cfg.graph)
            graph_rank()

        case "graph_statistics":
            g.params = d.common.placeholder(g.cfg.graph)
            graph_statistics()

        case "ranking":
            g.params = d.common.placeholder(g.cfg.ranking)
            pprint([
                "exec: lib.results.ranking.main()",
                c.results.ranking.main(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

        case "report":
            g.params = d.common.placeholder(g.cfg.report)
            pprint([
                "exec: lib.report.slackpost.main()",
                c.report.slackpost.main(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

        case "pdf":
            g.params = d.common.placeholder(g.cfg.report)
            g.params.update(filename=f"report_{sec}_{pattern}_{g.params["player_name"]}")
            pprint([
                "exec: lib.report.slackpost.results_report.gen_pdf()",
                c.report.slackpost.results_report.gen_pdf(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

        case "rating":
            g.params = d.common.placeholder(g.cfg.results)
            g.params.update(filename=f"rating_{sec}_{pattern}")
            pprint([
                "exec: lib.graph.rating.plot()",
                c.graph.rating.plot(),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)


def main():
    """メイン処理"""
    g.script_dir = os.path.dirname(os.path.abspath(__file__))
    configuration.setup()
    test_conf = configparser.ConfigParser()
    test_conf.read(g.args.testcase, encoding="utf-8")

    flag: dict = {
        "dump": test_conf["default"].getboolean("dump", False),
        "save": test_conf["default"].getboolean("save", False),
        "filename": "",
    }

    d.initialization.initialization_resultdb()
    c.member.read_memberslist(False)

    print("=" * 120)
    print(f"config  : {os.path.realpath(os.path.join(g.script_dir, g.args.config))}")
    print(f"database: {g.cfg.db.database_file}")

    for sec in test_conf.sections():
        print("=" * 120)
        print(f"[TEST CASE] {sec}")
        test_case = str()
        always_keyword = str()
        all_player = False
        target_player: list = []
        target_team: list = []
        flag.update(save=test_conf["default"].getboolean("save", False))

        for pattern, value in test_conf[sec].items():
            flag.update(filename=f"{sec}_{pattern}")
            match pattern:
                case s if re.match(r"^case", s):
                    test_case = value
                    continue
                case "target_player":
                    target_team.clear()
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
                    target_player.clear()
                    choice_list = [x["team"] for x in g.team_list]
                    for x in range(int(value)):
                        if not choice_list:
                            break
                        choice_name = random.choice(choice_list)
                        target_team.append(choice_name)
                        choice_list.remove(choice_name)
                    continue
                case s if re.match(r"^always_keyword", s):
                    always_keyword = value
                    print("always_keyword:", always_keyword)
                    continue
                case "save":
                    flag.update(save=test_conf[sec].getboolean("save"))
                    continue

            print("-" * 120)
            argument = f"{value} {always_keyword}"
            if test_conf[sec].getboolean("config", False):
                pprint(["*** config ***", vars(g.cfg)], width=120)

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
