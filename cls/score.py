"""
cls/score.py
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, cast

from cls.types import ScoreDataDict
from libs.functions.score import calculation_point


@dataclass
class Score:
    """プレイヤー成績"""
    name: str = field(default="")
    """プレイヤー名"""
    r_str: str = field(default="")
    """入力された素点情報(文字列)"""
    rpoint: int = field(default=0)
    """素点(入力文字列評価後)"""
    point: float = field(default=0.0)
    """獲得ポイント"""
    rank: int = field(default=0)
    """獲得順位"""

    def has_valid_data(self) -> bool:
        """有効なデータを持っているかチェック"""
        return self != Score()

    def to_dict(self, prefix: str | None = None) -> dict:
        """データを辞書で返す

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
    """タイムスタンプ"""
    p1: Score = field(default_factory=Score)
    """東家成績"""
    p2: Score = field(default_factory=Score)
    """南家成績"""
    p3: Score = field(default_factory=Score)
    """西家成績"""
    p4: Score = field(default_factory=Score)
    """北家成績"""
    comment: Optional[str] = field(default=None)
    """ゲームコメント"""
    deposit: int = field(default=0)
    """供託"""
    rule_version: str = field(default="")
    """ルールバージョン"""

    def __bool__(self) -> bool:
        return all([bool(x) for x in self.to_list()])

    def has_valid_data(self) -> bool:
        """有効なデータを持っているかチェック"""
        return all([
            self.ts != GameResult.ts,
            self.p1.has_valid_data(),
            self.p2.has_valid_data(),
            self.p3.has_valid_data(),
            self.p4.has_valid_data(),
            all(self.to_list("rank")),
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
                        if isinstance(v, (float, int)):
                            setattr(prefix_obj, "point", float(v))
                    case "rank":
                        if isinstance(v, int):
                            setattr(prefix_obj, "rank", int(v))

        if "ts" in kwargs:
            self.ts = kwargs["ts"]
        if "rule_version" in kwargs:
            self.rule_version = str(kwargs["rule_version"])
        if "deposit" in kwargs:
            self.deposit = int(kwargs["deposit"])
        if "comment" in kwargs:
            self.comment = kwargs["comment"]

    def to_dict(self) -> ScoreDataDict:
        """データを辞書で返す

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
        """データをテキストで返す

        Args:
            kind (Literal, optional): 表示形式
                - *simple* 簡易情報 (Default)
                - *detail* 詳細情報

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

    def to_list(self, kind: Literal["name", "str", "rpoint", "point", "rank"] = "name") -> list[str | int | float]:
        """指定データをリストで返す

        Args:
            kind (Literal, optional): 取得内容
                - *name*: プレイヤー名 (Default)
                - *str*: 入力された素点情報
                - *rpoint*: 素点
                - *point*: ポイント
                - *rank*: 順位

        Returns:
            list[str]: リスト
        """

        ret_list: list = []
        match kind:
            case "name":
                ret_list = [self.p1.name, self.p2.name, self.p3.name, self.p4.name]
            case "str":
                ret_list = [self.p1.r_str, self.p2.r_str, self.p3.r_str, self.p4.r_str]
            case "rpoint":
                ret_list = [self.p1.rpoint, self.p2.rpoint, self.p3.rpoint, self.p4.rpoint]
            case "point":
                ret_list = [self.p1.point, self.p2.point, self.p3.point, self.p4.point]
            case "point":
                ret_list = [self.p1.point, self.p2.point, self.p3.point, self.p4.point]
            case "rank":
                ret_list = [self.p1.rank, self.p2.rank, self.p3.rank, self.p4.rank]

        return ret_list

    def rpoint_sum(self) -> int:
        """素点合計

        Returns:
            int: 素点合計
        """

        if not all(self.to_list("rank")):  # 順位が確定していない場合は先に計算
            self.calc()

        return sum(cast(list[int], self.to_list("rpoint")))

    def calc(self, **kwargs):
        """獲得ポイント計算"""
        if kwargs:
            self.set(**kwargs)

        if all([self.p1.has_valid_data(), self.p2.has_valid_data(), self.p3.has_valid_data(), self.p4.has_valid_data()]):
            self.set(**calculation_point(self.to_list("str")))
