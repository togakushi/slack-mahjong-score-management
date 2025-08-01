#!/usr/bin/env python3
"""
test.py
"""

import configparser
import random
import re
from pprint import pprint

import libs.global_value as g
from cls.command import CommandParser
from integrations import factory
from libs.commands import graph, ranking, report, results
from libs.data import initialization
from libs.functions import compose, configuration
from libs.utils import dictutil


def test_pattern(flag: dict, test_case: str, sec: str, pattern: str, argument: str):
    """テストケース実行

    Args:
        flag (dict): フラグ格納辞書
        test_case (str): テストケース
        sec (str): 定義セクション
        pattern (str): 実行パターン
    """

    def graph_point(m):
        """ポイント推移グラフ"""
        if len(g.params["player_list"]) == 1:
            pprint([
                "exec: graph.personal.plot()",
                graph.personal.plot(m),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)
        else:
            graph.summary.point_plot(m)
            pprint([
                "exec: graph.summary.point_plot()",
                graph.summary.point_plot(m),
                f"{g.params=}" if flag.get("dump") else "g.params={...}",
            ], width=120)

    def graph_rank(m):
        """順位推移グラフ"""
        pprint([
            "exec: graph.summary.rank_plot()",
            graph.summary.point_plot(m),
            f"{g.params=}" if flag.get("dump") else "g.params={...}",
        ], width=120)

    def graph_statistics(m):
        """統計グラフ"""
        pprint([
            "exec: graph.personal.statistics_plot()",
            graph.personal.statistics_plot(m),
            f"{g.params=}" if flag.get("dump") else "g.params={...}",
        ], width=120)

    # ---------------------------------------------------------------------------------------------
    m = factory.select_parser("test", **g.cfg.setting.to_dict())
    target_loop: list = []

    if flag.get("target_loop"):
        target_loop += flag.get("target_player", [])
        target_loop += flag.get("target_team", [])
    else:
        target_loop = ["once"]
        argument += " ".join(flag.get("target_player", []))
        argument += " ".join(flag.get("target_team", []))

    for loop in target_loop:
        add_argument = argument.split()

        # 追加オプション
        pre_params = CommandParser().analysis_argument(add_argument).flags
        if flag.get("target_loop"):
            add_argument.append(f"{loop}")

        if flag.get("save"):
            if pre_params.get("filename"):
                pass
            else:
                if flag.get("target_loop"):
                    add_argument.append(f"filename:{sec}_{pattern}_{loop}")
                else:
                    add_argument.append(f"filename:{sec}_{pattern}")

        print("-" * 120)
        print(f"{pattern=} argument={add_argument}")

        match test_case:
            case "skip":
                pass

            case "member":
                pprint(g.member_list)
                pprint(g.team_list)

            case "help":
                pprint(compose.msg_help.event_message(), width=200)

            case "summary":
                g.cfg.results.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.results, m)
                pprint([
                    "exec: results.summary.aggregate()",
                    results.summary.aggregation(m),
                    f"{g.params=}" if flag.get("dump") else "g.params={...}",
                ], width=120)

            case "graph":
                g.cfg.graph.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.graph, m)
                if g.params.get("filename"):
                    save_filename = g.params["filename"]
                    g.params.update(filename=f"{save_filename}_point")
                    graph_point(m)
                    g.params.update(filename=f"{save_filename}_rank")
                    graph_rank(m)
                    if g.params.get("statistics"):
                        g.params.update(filename=f"{save_filename}")
                        graph_statistics(m)
                else:
                    g.params.update(filename=f"point_{sec}_{pattern}")
                    graph_point(m)
                    g.params.update(filename=f"rank_{sec}_{pattern}")
                    graph_rank(m)
                    if g.params.get("statistics"):
                        g.params.update(filename=f"statistics_{sec}_{pattern}")
                        graph_statistics(m)

            case "graph_point":
                g.cfg.graph.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.graph, m)
                graph_point(m)

            case "graph_rank":
                g.cfg.graph.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.graph, m)
                graph_rank(m)

            case "graph_statistics":
                g.cfg.graph.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.graph, m)
                graph_statistics(m)

            case "ranking":
                g.cfg.ranking.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.ranking, m)

                pprint([
                    "exec: ranking.ranking.aggregation()",
                    ranking.ranking.aggregation(m),
                    f"{g.params=}" if flag.get("dump") else "g.params={...}",
                ], width=120)

            case "report":
                g.cfg.report.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.report, m)
                pprint([
                    "exec: report.results_list.main()",
                    report.results_list.main(m),
                    f"{g.params=}" if flag.get("dump") else "g.params={...}",
                ], width=120)

            case "pdf":
                g.cfg.report.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.report, m)
                pprint([
                    "exec: report.slackpost.results_report.gen_pdf()",
                    report.results_report.gen_pdf(m),
                    f"{g.params=}" if flag.get("dump") else "g.params={...}",
                ], width=120)

            case "rating":
                g.cfg.results.always_argument = add_argument
                g.params = dictutil.placeholder(g.cfg.results, m)
                pprint([
                    "exec: graph.rating.plot()",
                    graph.rating.plot(m),
                    f"{g.params=}" if flag.get("dump") else "g.params={...}",
                ], width=120)


def main():
    """メイン処理"""
    configuration.setup()
    test_conf = configparser.ConfigParser()
    test_conf.read(g.args.testcase, encoding="utf-8")

    flag: dict = {}

    initialization.initialization_resultdb()
    initialization.read_grade_table()
    configuration.read_memberslist(False)

    for sec in test_conf.sections():
        print("=" * 120)
        print(f"[TEST CASE] {sec}")
        test_case = str()
        always_keyword = str()
        flag.clear()
        flag.update(target_player=[])
        flag.update(target_team=[])
        flag.update(target_loop=False)
        flag.update(dump=test_conf["default"].getboolean("dump", False))
        flag.update(save=test_conf["default"].getboolean("save", False))

        for pattern, value in test_conf[sec].items():
            flag.update(filename=f"{sec}_{pattern}")
            match pattern:
                case s if re.match(r"^case", s):
                    test_case = value
                    continue
                case "target_player":
                    flag["target_team"].clear()
                    choice_list = list(set(g.member_list.values()))
                    for x in range(int(value)):
                        if not choice_list:
                            break
                        choice_name = random.choice(choice_list)
                        flag["target_player"].append(choice_name)
                        choice_list.remove(choice_name)
                    continue
                case "target_team":
                    flag["target_player"].clear()
                    choice_list = [x["team"] for x in g.team_list]
                    for _ in range(int(value)):
                        if not choice_list:
                            break
                        choice_name = random.choice(choice_list)
                        flag["target_team"].append(choice_name)
                        choice_list.remove(choice_name)
                    continue
                case "target_loop":
                    flag.update(target_loop=test_conf[sec].getboolean("target_loop"))
                    continue
                case s if re.match(r"^always_keyword", s):
                    always_keyword = value
                    print("always_keyword:", always_keyword)
                    continue
                case "save":
                    flag.update(save=test_conf[sec].getboolean("save"))
                    continue

            argument = f"{value} {always_keyword} "
            if test_conf[sec].getboolean("config", False):
                pprint(["*** config ***", vars(g.cfg)], width=120)

            test_pattern(flag, test_case, sec, pattern, argument)


if __name__ == "__main__":
    main()
