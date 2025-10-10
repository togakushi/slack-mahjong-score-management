"""
libs/datamodels.py
"""

from dataclasses import dataclass, field
from typing import Optional

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import loader


@dataclass
class GameInfo:
    """ゲーム集計情報"""

    count: int = field(default=0)
    """ゲーム数"""
    first_game: Optional[ExtDt] = field(default=None)
    """記録されている最初のゲーム時間"""
    last_game: Optional[ExtDt] = field(default=None)
    """記録されている最後のゲーム時間"""
    first_comment: Optional[str] = field(default=None)
    """記録されている最初のゲームコメント"""
    last_comment: Optional[str] = field(default=None)
    """記録されている最後のゲームコメント"""

    def __post_init__(self):
        self.get()

    def get(self):
        """指定条件を満たすゲーム数のカウント、最初と最後の時刻とコメントを取得"""

        # グローバルパラメータチェック
        if "rule_version" not in g.params:
            g.params.update(rule_version=g.cfg.mahjong.rule_version)
        if "starttime" not in g.params:
            g.params.update(starttime=ExtDt().range("全部").start)
        if "endtime" not in g.params:
            g.params.update(endtime=ExtDt().range("全部").end)

        # データ収集
        df = loader.read_data("GAME_INFO")
        self.count = int(df["count"].to_string(index=False))

        if self.count >= 1:
            # プレイ時間
            self.first_game = ExtDt(str(df.at[0, "first_game"]))
            self.last_game = ExtDt(str(df.at[0, "last_game"]))
            # コメント
            if (first_comment := df.at[0, "first_comment"]):
                self.first_comment = str(first_comment)
            if (last_comment := df.at[0, "last_comment"]):
                self.last_comment = str(last_comment)
        else:
            self.first_game = ExtDt()
            self.last_game = ExtDt()

        # 規定打数更新
        if not g.params.get("stipulated", 0):
            match g.params.get("command", ""):
                case "results":
                    g.params["stipulated"] = g.cfg.results.stipulated_calculation(self.count)
                case "graph":
                    g.params["stipulated"] = g.cfg.graph.stipulated_calculation(self.count)
                case "ranking":
                    g.params["stipulated"] = g.cfg.ranking.stipulated_calculation(self.count)
                case "report":
                    g.params["stipulated"] = g.cfg.report.stipulated_calculation(self.count)

    def clear(self):
        """情報削除"""

        self.count = 0
        self.first_game = None
        self.first_comment = None
        self.last_game = None
        self.last_comment = None

    def conditions(self) -> dict:
        """検索条件を返す"""

        return {
            "rule_version": g.params.get("rule_version"),
            "starttime": g.params.get("starttime"),
            "endtime": g.params.get("endtime"),
        }
