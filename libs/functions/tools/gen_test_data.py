"""
libs/functions/tools/gen_test_data.py
"""

import itertools
import logging
import random
from contextlib import closing
from datetime import datetime
from typing import cast

from tqdm import tqdm

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs import configuration
from libs.functions.tools import score_simulator
from libs.utils import dbutil


def main(season_times: int = 1):
    """テスト用ゲーム結果生成処理

    Args:
        season_times (int, optional): 総当たり回数. Defaults to 1.
    """

    configuration.read_memberslist(log=False)

    # 対戦組み合わせ作成
    teams: list = [x["team"] for x in g.cfg.team.list]
    position: list = ["先鋒", "次鋒", "中堅", "副将", "大将"]
    teams_data: dict = {x["team"]: x["member"] for x in g.cfg.team.list}
    matchup: list = list(itertools.combinations(teams, 4))
    teams_count: dict = {x: 0 for x in teams}
    total_count: int = 0

    now = datetime.now().timestamp() - ((len(matchup) + 7) * 86400 * season_times)
    dt = now

    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        cur.execute("delete from result;")
        for season in range(1, season_times + 1):
            random.shuffle(matchup)
            for count, game in tqdm(enumerate(matchup), total=len(matchup), desc=f"season({season}/{season_times})"):
                # 対戦メンバーの決定
                vs_member = {}
                for team_name in game:
                    teams_count[team_name] += 1
                    team_member = teams_data[team_name]
                    random.shuffle(team_member)
                    vs_member[team_name] = team_member

                # 試合結果
                total_count += 1
                team_name = list(game)
                random.shuffle(team_name)
                for idx in range(5):
                    # 席順シャッフル
                    member = [
                        vs_member[team_name[0]][idx],
                        vs_member[team_name[1]][idx],
                        vs_member[team_name[2]][idx],
                        vs_member[team_name[3]][idx],
                    ]
                    random.shuffle(member)

                    # スコアデータ生成
                    dt = now + total_count * 86400 + idx * 3600 + random.random()
                    vs_score = score_simulator.simulate_game()
                    result = GameResult(
                        ts=str(dt),
                        p1_name=member[0],
                        p1_str=str(int(vs_score[0] / 100)),
                        p2_name=member[1],
                        p2_str=str(int(vs_score[1] / 100)),
                        p3_name=member[2],
                        p3_str=str(int(vs_score[2] / 100)),
                        p4_name=member[3],
                        p4_str=str(int(vs_score[3] / 100)),
                        comment=f"第{season:02d}期{count + 1:04d}試合_{position[idx]}戦",
                        rule_version=g.cfg.mahjong.rule_version,
                    )

                    # データ投入
                    param = {
                        "playtime": ExtDt(dt).format("sql"),
                    }
                    param.update(cast(dict, result.to_dict()))
                    cur.execute(dbutil.query("RESULT_INSERT"), param)

                    output = f"{position[idx]}: "
                    output += result.to_text("detail")
                    logging.debug(output)

        cur.commit()

    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        rows = cur.execute("select name, round(sum(point), 1) as point from team_results group by name order by point desc;")
        logging.info(dict(rows.fetchall()))
