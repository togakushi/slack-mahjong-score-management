"""
libs/functions/tools/gen_test_data.py
"""

import itertools
import logging
import random
import sqlite3
from contextlib import closing
from datetime import datetime

import libs.global_value as g
from libs.functions import configuration, score
from libs.functions.tools import score_simulator


def main(season_times: int = 1):
    """テスト用ゲーム結果生成処理

    Args:
        season_times (int, optional): 総当たり回数. Defaults to 1.
    """

    configuration.read_memberslist(log=False)

    # 対戦組み合わせ作成
    teams: list = [x["team"] for x in g.team_list]
    position: list = ["先鋒", "次鋒", "中堅", "副将", "大将"]
    teams_data: dict = {x["team"]: x["member"].split(",") for x in g.team_list}
    matchup: list = list(itertools.combinations(teams, 4))
    teams_count: dict = {x: 0 for x in teams}
    total_count: int = 0

    print(f"{g.team_list=}")
    print(f"{teams_data=}")

    now = datetime.now().timestamp() - ((len(matchup) + 7) * 86400 * season_times)
    dt = now
    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        cur.execute("delete from result;")
        for season in range(1, season_times + 1):
            random.shuffle(matchup)
            for count, game in enumerate(matchup):
                print(f">>> 第{season:02d}期 {count + 1:04d}試合 /", datetime.fromtimestamp(dt).strftime("%Y-%m-%d"))
                # 対戦メンバーの決定
                vs_member = {}
                for team_name in game:
                    teams_count[team_name] += 1
                    team_member = teams_data[team_name]
                    random.shuffle(team_member)
                    vs_member[team_name] = team_member
                # print(game, vs_member)

                # 試合結果
                total_count += 1
                team_name = list(game)
                random.shuffle(team_name)
                for idx in range(5):
                    member = [
                        vs_member[team_name[0]][idx],
                        vs_member[team_name[1]][idx],
                        vs_member[team_name[2]][idx],
                        vs_member[team_name[3]][idx],
                    ]
                    random.shuffle(member)
                    param = {}
                    vs_score = score_simulator.simulate_game()
                    result = score.get_score([
                        member[0], str(int(vs_score[0] / 100)),
                        member[1], str(int(vs_score[1] / 100)),
                        member[2], str(int(vs_score[2] / 100)),
                        member[3], str(int(vs_score[3] / 100)),
                        f"第{season:02d}期{count + 1:04d}試合_{position[idx]}戦",
                    ])

                    # データ投入
                    dt = now + total_count * 86400 + idx * 3600 + random.random()
                    param = {
                        "ts": str(dt),
                        "playtime": datetime.fromtimestamp(dt).strftime("%Y-%m-%d %H:%M:%S.%f"),
                        "rule_version": g.cfg.mahjong.rule_version,
                    }
                    param.update(result)
                    cur.execute(g.sql["RESULT_INSERT"], param)

                    output = f"{position[idx]}: "
                    output += f"[{result["p1_rank"]}位 {result["p1_name"]} / {result["p1_rpoint"] * 100} ({result["p1_point"]}pt)] "
                    output += f"[{result["p2_rank"]}位 {result["p2_name"]} / {result["p2_rpoint"] * 100} ({result["p2_point"]}pt)] "
                    output += f"[{result["p3_rank"]}位 {result["p3_name"]} / {result["p3_rpoint"] * 100} ({result["p3_point"]}pt)] "
                    output += f"[{result["p4_rank"]}位 {result["p4_name"]} / {result["p4_rpoint"] * 100} ({result["p4_point"]}pt)] "
                    logging.debug(output)

        cur.commit()

    logging.notice(teams_count)  # type: ignore
