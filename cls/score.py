"""
cls/score.py
"""

from dataclasses import dataclass, field
from typing import Optional, cast

from cls.types import ScoreDataDict
from libs.functions.score import get_score


@dataclass
class Score:
    """個人成績"""
    name: str = field(default="")
    r_str: str = field(default="")
    rpoint: int = field(default=0)
    point: float = field(default=0.0)
    rank: int = field(default=0)

    def is_default(self) -> bool:
        return self == Score()

    def to_dict(self, prefix: str | None = None) -> dict:
        ret_dict: dict = {}
        prefix = "" if prefix is None else f"{prefix}_"
        for k, v in self.__dict__.items():
            if k == "r_str":
                k = "str"
            ret_dict[f"{prefix}{k}"] = v

        return ret_dict


@dataclass
class GameResult:
    """ゲーム結果"""
    ts: str = field(default="")
    p1: Score = field(default_factory=Score)
    p2: Score = field(default_factory=Score)
    p3: Score = field(default_factory=Score)
    p4: Score = field(default_factory=Score)
    comment: Optional[str] = field(default=None)
    deposit: int = field(default=0)
    rule_version: str = field(default="")

    def is_default(self) -> bool:
        """更新チェック"""
        return all([
            self.ts == GameResult.ts,
            self.comment == GameResult.comment,
            self.p1.is_default(),
            self.p2.is_default(),
            self.p3.is_default(),
            self.p4.is_default(),
        ])

    def set(self, data: ScoreDataDict) -> None:
        """スコア取り込み

        Args:
            data (ScoreDataDict): スコアデータ
        """
        for prefix in ("p1", "p2", "p3", "p4"):
            x = {str(k).replace(f"{prefix}_", ""): v for k, v in data.items() if str(k).startswith(f"{prefix}_")}
            prefix_obj = getattr(self, prefix)
            for k, v in x.items():
                match k:
                    case "name":
                        setattr(prefix_obj, "name", str(v))
                    case "str" | "r_str":
                        setattr(prefix_obj, "r_str", str(v))
                    case "rpoint":
                        setattr(prefix_obj, "rpoint", int(v))
                    case "point":
                        setattr(prefix_obj, "point", float(v))
                    case "rank":
                        setattr(prefix_obj, "rank", int(v))

        if "ts" in data:
            self.ts = data["ts"]
        if "rule_version" in data:
            self.rule_version = data["rule_version"]
        if "deposit" in data:
            self.deposit = data["deposit"]
        if "comment" in data:
            self.comment = data["comment"]

    def to_dict(self) -> ScoreDataDict:
        """辞書で返す

        Returns:
            ScoreDataDict: スコアデータ
        """

        ret_dict: dict = {}
        ret_dict.update(ts=self.ts)
        ret_dict.update(comment=self.comment)
        ret_dict.update(rule_version=self.rule_version)
        ret_dict.update(deposit=self.deposit)
        ret_dict.update(self.p1.to_dict("p1"))
        ret_dict.update(self.p2.to_dict("p2"))
        ret_dict.update(self.p3.to_dict("p3"))
        ret_dict.update(self.p4.to_dict("p4"))

        return cast(ScoreDataDict, ret_dict)

    def to_text(self, detail: bool = False) -> str:
        """テキストで返す

        Args:
            detail (bool, optional): 出力切替. Defaults to False.

        Returns:
            str: スコアデータ
        """

        ret_text: str = ""
        if detail:
            ret_text += f"[{self.p1.rank}位 {self.p1.name} / {self.p1.rpoint * 100} ({self.p1.point}pt)] "
            ret_text += f"[{self.p2.rank}位 {self.p2.name} / {self.p2.rpoint * 100} ({self.p2.point}pt)] "
            ret_text += f"[{self.p3.rank}位 {self.p3.name} / {self.p3.rpoint * 100} ({self.p3.point}pt)] "
            ret_text += f"[{self.p4.rank}位 {self.p4.name} / {self.p4.rpoint * 100} ({self.p4.point}pt)] "
            ret_text += f"[{self.comment if self.comment else ""}]"
        else:
            ret_text += f"[{self.p1.name} {self.p1.r_str}]"
            ret_text += f"[{self.p2.name} {self.p2.r_str}]"
            ret_text += f"[{self.p3.name} {self.p3.r_str}]"
            ret_text += f"[{self.p4.name} {self.p4.r_str}]"
            ret_text += f"[{self.comment if self.comment else ""}]"

        return ret_text

    def calc(self):
        """順位点計算"""
        self.set(get_score(self.to_dict()))

    def player_list(self) -> list[str]:
        """プレイヤーリスト

        Returns:
            list[str]: リスト
        """

        return [self.p1.name, self.p2.name, self.p3.name, self.p4.name]

    def rpoint_sum(self) -> int:
        """素点合計

        Returns:
            int: 素点合計
        """

        self.calc()

        return sum([self.p1.rpoint, self.p2.rpoint, self.p3.rpoint, self.p4.rpoint])
