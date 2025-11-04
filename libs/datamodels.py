"""
libs/datamodels.py
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional, Union

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import loader

if TYPE_CHECKING:
    from cls.score import GameResult
    from integrations.base.interface import MessageParserProtocol
    from libs.types import RemarkDict


@dataclass
class GameInfo:
    """ゲーム集計情報"""

    count: int = field(default=0)
    """集計範囲のゲーム数"""
    first_game: Optional[ExtDt] = field(default=None)
    """集計範囲の最初のゲーム時間"""
    last_game: Optional[ExtDt] = field(default=None)
    """集計範囲の最後のゲーム時間"""
    first_comment: Optional[str] = field(default=None)
    """集計範囲の最初のゲームコメント"""
    last_comment: Optional[str] = field(default=None)
    """集計範囲の最後のゲームコメント"""
    unique_name: int = field(default=0)
    """集計範囲のユニークプレイヤー数"""
    unique_team: int = field(default=0)
    """集計範囲のユニークチーム数"""

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
        self.unique_name = int(df["unique_name"].to_string(index=False))
        self.unique_team = int(df["unique_team"].to_string(index=False))

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
        if not g.params.get("stipulated", 0):  # 規定打数0はレートから計算
            match g.params.get("command", ""):
                case "results":
                    g.params["stipulated"] = g.cfg.results.stipulated_calculation(self.count)
                case "graph":
                    g.params["stipulated"] = g.cfg.graph.stipulated_calculation(self.count)
                case "ranking":
                    g.params["stipulated"] = g.cfg.ranking.stipulated_calculation(self.count)
                case "report":
                    g.params["stipulated"] = g.cfg.report.stipulated_calculation(self.count)

        logging.debug(self)

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


@dataclass
class ComparisonResults:
    """突合結果"""

    search_after: int = field(default=-7)
    """突合範囲(日数)"""
    score_list: dict[str, "MessageParserProtocol"] = field(default_factory=dict)
    """スコアリスト(一時保管用)"""

    mismatch: list[dict[str, "GameResult"]] = field(default_factory=list)
    """スコア差分"""
    missing: list["GameResult"] = field(default_factory=list)
    """スコア追加"""
    delete: list["GameResult"] = field(default_factory=list)
    """スコア削除"""
    remark_mod: list["RemarkDict"] = field(default_factory=list)
    """メモ変更"""
    remark_del: list["RemarkDict"] = field(default_factory=list)
    """メモ削除"""
    invalid_score: list["GameResult"] = field(default_factory=list)
    """素点合計不一致"""
    pending: list["GameResult"] = field(default_factory=list)
    """処理保留データ"""

    @property
    def after(self) -> ExtDt:
        """突合開始日時"""
        return ExtDt(days=self.search_after)

    @property
    def before(self) -> ExtDt:
        """突合終了日時"""
        return ExtDt()

    def output(
        self,
        kind: Literal["headline", "pending", "mismatch", "missing", "delete", "remark_mod", "remark_del", "invalid_score"]
    ) -> str:
        """出力メッセージ生成

        Args:
            kind (Literal[headline, pending, mismatch, missing, delete, remark_mod, remark_del, invalid_score]): 種類

        Returns:
            str: 生成文字列
        """

        ret: str = ""
        score: Union[dict, "GameResult"]
        match kind:
            case "headline":
                ret = f"突合範囲：{self.after.format("ymdhms")} - {self.before.format("ymdhms")}"
            case "pending":
                ret += f"＊ 保留：{len(self.pending)}件\n"
                for score in self.pending:
                    ret += f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text()}\n"
            case "mismatch":
                ret += f"＊ 不一致：{len(self.mismatch)}件\n"
                for score in self.mismatch:
                    ret += f"{ExtDt(float(score["before"].ts)).format("ymdhms")}\n"
                    ret += f"\t修正前：{score["before"].to_text()}\n"
                    ret += f"\t修正後：{score["after"].to_text()}\n"
            case "missing":
                ret += f"＊ 取りこぼし：{len(self.missing)}件\n"
                for score in self.missing:
                    ret += f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text()}\n"
            case "delete":
                ret += f"＊ 削除漏れ：{len(self.delete)}件\n"
                for score in self.delete:
                    ret += f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text()}\n"
            case "remark_mod":
                ret += f"＊ メモ更新：{len(self.remark_mod)}件\n"
                for remark in self.remark_mod:
                    ret += f"{ExtDt(float(remark["thread_ts"])).format("ymdhms")} "
                    ret += f"{remark["name"]} {remark["matter"]}\n"
            case "remark_del":
                ret += f"＊ メモ削除：{len(self.remark_del)}件\n"
            case "invalid_score":
                ret += f"＊ 素点合計不一致：{len(self.invalid_score)}件\n"
                for score in self.invalid_score:
                    ret += f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text()}\n"

        return ret
