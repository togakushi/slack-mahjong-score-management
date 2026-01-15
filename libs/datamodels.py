"""
libs/datamodels.py
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional, Union

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.timekit import Format
from libs.data import loader

if TYPE_CHECKING:
    import pandas as pd

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
            g.params.update({"rule_version": g.cfg.mahjong.rule_version})
        if "starttime" not in g.params:
            g.params.update({"starttime": ExtDt().range("全部").start})
        if "endtime" not in g.params:
            g.params.update({"endtime": ExtDt().range("全部").end})

        # データ収集
        df = loader.read_data("GAME_INFO")
        if df.empty:
            self.count = 0
            self.first_game = ExtDt()
            self.last_game = ExtDt()
            self.first_comment = ""
            self.last_comment = ""
            self.unique_name = 0
            self.unique_team = 0
        else:
            self.count = int(df["count"].to_string(index=False))
            self.first_game = ExtDt(df["first_game"].to_string(index=False))
            self.last_game = ExtDt(df["last_game"].to_string(index=False))
            self.first_comment = str(df["first_comment"].to_string(index=False))
            self.last_comment = str(df["last_comment"].to_string(index=False))
            self.unique_name = int(df["unique_name"].to_string(index=False))
            self.unique_team = int(df["unique_team"].to_string(index=False))

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
class ResultsInfo:
    """成績情報"""

    @dataclass
    class ResultsDetailed:
        """詳細データ"""

        mode: Literal[3, 4] = field(default=4)
        """集計モード"""
        win: int = field(default=0)
        """勝ち数"""
        lose: int = field(default=0)
        """負け数"""
        draw: int = field(default=0)
        """引き分け数"""
        total_point: float = field(default=0)
        """通算ポイント"""
        avg_point: float = field(default=0)
        """平均ポイント"""

        rank1: int = field(default=0)
        """1位獲得数"""
        rank2: int = field(default=0)
        """2位獲得数"""
        rank3: int = field(default=0)
        """3位獲得数"""
        rank4: int = field(default=0)
        """4位獲得数"""
        flying: int = field(default=0)
        """トビ数"""
        yakuman: int = field(default=0)
        """役満和了数"""

        # 集計範囲
        first_game: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
        """最初の記録時間"""
        last_game: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
        """最後の記録時間"""
        first_comment: Optional[str] = field(default=None)
        """最初の記録時間のコメント"""
        last_comment: Optional[str] = field(default=None)
        """最後の記録時間のコメント"""

        @property
        def count(self) -> int:
            match self.mode:
                case 3:
                    return sum([self.rank1, self.rank2, self.rank3])
                case 4:
                    return sum([self.rank1, self.rank2, self.rank3, self.rank4])

        @property
        def rank_avg(self) -> float:
            if self.count:
                match self.mode:
                    case 3:
                        return round((self.rank1 + self.rank2 * 2 + self.rank3 * 3) / self.count, 2)
                    case 4:
                        return round((self.rank1 + self.rank2 * 2 + self.rank3 * 3 + self.rank4 * 4) / self.count, 2)
            return 0.00

        @property
        def rank_distr(self) -> str:
            match self.mode:
                case 3:
                    return f"{self.rank1}-{self.rank2}-{self.rank3} ({self.rank_avg:.2f})"
                case 4:
                    return f"{self.rank1}-{self.rank2}-{self.rank3}-{self.rank4} ({self.rank_avg:.2f})"

        @property
        def rank_distr2(self) -> str:
            match self.mode:
                case 3:
                    return f"{self.rank1}+{self.rank2}+{self.rank3}={self.count}"
                case 4:
                    return f"{self.rank1}+{self.rank2}+{self.rank3}+{self.rank4}={self.count}"

        @property
        def rank1_rate(self) -> float:
            return round(self.rank1 / self.count, 2)

        @property
        def rank2_rate(self) -> float:
            return round(self.rank2 / self.count, 2)

        @property
        def rank3_rate(self) -> float:
            return round(self.rank3 / self.count, 2)

        @property
        def rank4_rate(self) -> float:
            return round(self.rank4 / self.count, 2)

        @property
        def flying_rate(self) -> float:
            return round(self.flying / self.count, 2)

        @property
        def yakuman_rate(self) -> float:
            return round(self.yakuman / self.count, 2)

    mode: Literal[3, 4] = field(default=4)
    """集計モード"""
    name: str = field(default="")
    """プレイヤー名/チーム名"""

    # 統計データ
    seat0: ResultsDetailed = field(default_factory=ResultsDetailed)
    """全席"""
    seat1: ResultsDetailed = field(default_factory=ResultsDetailed)
    """東家"""
    seat2: ResultsDetailed = field(default_factory=ResultsDetailed)
    """南家"""
    seat3: ResultsDetailed = field(default_factory=ResultsDetailed)
    """西家"""
    seat4: ResultsDetailed = field(default_factory=ResultsDetailed)
    """北家"""

    # 検索条件
    rule_version: list = field(default_factory=list)
    """ルールセット"""
    # 検索範囲
    starttime: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
    endtime: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))

    # 検索ワード
    search_word: str = field(default="")

    def set_data(self, df: "pd.DataFrame"):
        """集計結果取り込み

        Args:
            df (pd.DataFrame): 集計結果
        """

        def _set_values(work: ResultsInfo.ResultsDetailed, data: dict):
            work.win = int(data.get("win", 0))
            work.lose = int(data.get("lose", 0))
            work.draw = int(data.get("draw", 0))
            work.total_point = float(data.get("total_point", 0.0))
            work.avg_point = float(data.get("avg_point", 0.0))
            work.rank1 = int(data.get("rank1", 0))
            work.rank2 = int(data.get("rank2", 0))
            work.rank3 = int(data.get("rank3", 0))
            work.rank4 = int(data.get("rank4", 0))
            work.flying = int(data.get("flying", 0))
            work.yakuman = int(data.get("yakuman", 0))
            work.first_game = ExtDt(data.get("first_game"))
            work.last_game = ExtDt(data.get("last_game"))
            work.first_comment = data.get("first_comment")
            work.last_comment = data.get("last_comment")

        for idx, data in df.to_dict(orient="index").items():
            match idx:
                case 0:
                    _set_values(self.seat0, data)
                case 1:
                    _set_values(self.seat1, data)
                case 2:
                    _set_values(self.seat2, data)
                case 3:
                    _set_values(self.seat3, data)
                case 4:
                    _set_values(self.seat4, data)

    def set_parameter(self, **kwargs):
        if "mode" in kwargs and isinstance(kwargs["mode"], int):
            if kwargs["mode"] in (3, 4):
                self.mode = kwargs["mode"]  # type: ignore[assignment]
                self.seat0.mode = self.mode
                self.seat1.mode = self.mode
                self.seat2.mode = self.mode
                self.seat3.mode = self.mode
                self.seat4.mode = self.mode
            else:
                RuntimeError
        if "player_name" in kwargs and isinstance(kwargs["player_name"], str):
            self.name = kwargs["player_name"]
        if "starttime" in kwargs and isinstance(kwargs["starttime"], (ExtDt, str)):
            self.starttime = ExtDt(kwargs["starttime"])
        if "endtime" in kwargs and isinstance(kwargs["endtime"], (ExtDt, str)):
            self.endtime = ExtDt(kwargs["endtime"])
        if "search_word" in kwargs and isinstance(kwargs["search_word"], str):
            self.search_word = kwargs["search_word"]


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
        return ExtDt(days=self.search_after, hours=g.cfg.setting.time_adjust)

    @property
    def before(self) -> ExtDt:
        """突合終了日時"""
        return ExtDt()

    def output(
        self,
        kind: Literal[
            "summary",
            "headline",
            "pending",
            "mismatch",
            "missing",
            "delete",
            "remark_mod",
            "remark_del",
            "invalid_score",
        ],
    ) -> str:
        """出力メッセージ生成

        Args:
            kind (Literal[summary, headline, pending, mismatch, missing, delete, remark_mod, remark_del, invalid_score]): 種類

        Returns:
            str: 生成文字列
        """  # noqa: E501

        ret: str = ""
        score: Union[dict, "GameResult"]
        match kind:
            case "summary":
                ret += f"pending:{len(self.pending)} "
                ret += f"mismatch:{len(self.mismatch)} "
                ret += f"missing:{len(self.missing)} "
                ret += f"delete:{len(self.delete)} "
                ret += f"remark_mod:{len(self.remark_mod)} "
                ret += f"remark_del:{len(self.remark_del)} "
                ret += f"invalid_score:{len(self.invalid_score)} "
            case "headline":
                ret = f"突合範囲：{self.after.format(Format.YMDHMS)} - {self.before.format(Format.YMDHMS)}"
            case "pending":
                ret += f"＊ 保留：{len(self.pending)}件\n"
                for score in self.pending:
                    ret += f"{ExtDt(float(score.ts)).format(Format.YMDHMS)} {score.to_text()}\n"
            case "mismatch":
                ret += f"＊ 不一致：{len(self.mismatch)}件\n"
                for score in self.mismatch:
                    ret += f"{ExtDt(float(score['before'].ts)).format(Format.YMDHMS)}\n"
                    ret += f"\t修正前：{score['before'].to_text()}\n"
                    ret += f"\t修正後：{score['after'].to_text()}\n"
            case "missing":
                ret += f"＊ 取りこぼし：{len(self.missing)}件\n"
                for score in self.missing:
                    ret += f"{ExtDt(float(score.ts)).format(Format.YMDHMS)} {score.to_text()}\n"
            case "delete":
                ret += f"＊ 削除漏れ：{len(self.delete)}件\n"
                for score in self.delete:
                    ret += f"{ExtDt(float(score.ts)).format(Format.YMDHMS)} {score.to_text()}\n"
            case "remark_mod":
                ret += f"＊ メモ更新：{len(self.remark_mod)}件\n"
                for remark in self.remark_mod:
                    ret += f"{ExtDt(float(remark['thread_ts'])).format(Format.YMDHMS)} "
                    ret += f"{remark['name']} {remark['matter']}\n"
            case "remark_del":
                ret += f"＊ メモ削除：{len(self.remark_del)}件\n"
            case "invalid_score":
                ret += f"＊ 素点合計不一致：{len(self.invalid_score)}件\n"
                for score in self.invalid_score:
                    ret += f"{ExtDt(float(score.ts)).format(Format.YMDHMS)} {score.to_text()}\n"

        return ret
