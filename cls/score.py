"""
cls/score.py
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

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
        """更新チェック"""
        return self == Score()

    def to_dict(self, prefix: str | None = None) -> dict:
        """辞書で返す

        Args:
            prefix (str | None, optional): キーに付与する接頭辞. Defaults to None.

        Returns:
            dict: 返却する辞書
        """

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

    def set(self, **kwargs) -> None:
        """テータ取り込み"""
        for prefix in ("p1", "p2", "p3", "p4"):
            x = {str(k).replace(f"{prefix}_", ""): v for k, v in kwargs.items() if str(k).startswith(f"{prefix}_")}
            prefix_obj = getattr(self, prefix)
            for k, v in x.items():
                match k:
                    case "name":
                        setattr(prefix_obj, "name", str(v))
                    case "str" | "r_str":
                        setattr(prefix_obj, "r_str", str(v))
                    case "rpoint":
                        if isinstance(v, int):
                            setattr(prefix_obj, "rpoint", int(v))
                    case "point":
                        if isinstance(v, float):
                            setattr(prefix_obj, "point", float(v))
                    case "rank":
                        if isinstance(v, int):
                            setattr(prefix_obj, "rank", int(v))

        if "ts" in kwargs:
            self.ts = kwargs["ts"]
        if "rule_version" in kwargs:
            self.rule_version = kwargs["rule_version"]
        if "deposit" in kwargs:
            self.deposit = kwargs["deposit"]
        if "comment" in kwargs:
            self.comment = kwargs["comment"]

    def to_dict(self) -> ScoreDataDict:
        """辞書で返す

        Returns:
            ScoreDataDict: スコアデータ
        """

        ret_dict: ScoreDataDict = {}
        ret_dict.update({
            "ts": self.ts,
            "comment": self.comment,
            "rule_version": self.rule_version,
            "deposit": self.deposit,
            **self.p1.to_dict("p1"),
            **self.p2.to_dict("p2"),
            **self.p3.to_dict("p3"),
            **self.p4.to_dict("p4"),
        })

        return ret_dict

    def to_text(self, kind: Literal["simple", "detail"] = "simple") -> str:
        """テキストで返す

        Args:
            kind (Literal["simple", "detail"], optional): 表示形式. Defaults to "simple".

        Returns:
            str: スコアデータ
        """

        ret_text: str = ""
        match kind:
            case "simple":
                ret_text += f"[{self.p1.name} {self.p1.r_str}]"
                ret_text += f"[{self.p2.name} {self.p2.r_str}]"
                ret_text += f"[{self.p3.name} {self.p3.r_str}]"
                ret_text += f"[{self.p4.name} {self.p4.r_str}]"
                ret_text += f"[{self.comment if self.comment else ""}]"
            case "detail":
                ret_text += f"[{self.p1.rank}位 {self.p1.name} {self.p1.rpoint * 100}点 ({self.p1.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p2.rank}位 {self.p2.name} {self.p2.rpoint * 100}点 ({self.p2.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p3.rank}位 {self.p3.name} {self.p3.rpoint * 100}点 ({self.p3.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p4.rank}位 {self.p4.name} {self.p4.rpoint * 100}点 ({self.p4.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.comment if self.comment else ""}]"

        return ret_text

    def calc(self):
        """順位点計算"""
        self.set(**get_score(self.to_dict()))

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
