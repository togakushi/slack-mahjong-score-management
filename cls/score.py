"""
cls/score.py
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional, cast

import pandas as pd

if TYPE_CHECKING:
    from libs.types import ScoreDict


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

    def to_dict(self, prefix: str) -> "ScoreDict":
        """データを辞書で返す

        Args:
            prefix (str): キーに付与する接頭辞

        Returns:
            ScoreDict: 返却する辞書
        """

        return cast(
            "ScoreDict",
            {
                f"{prefix}_name": self.name,
                f"{prefix}_str": self.r_str,
                f"{prefix}_rpoint": self.rpoint,
                f"{prefix}_point": self.point,
                f"{prefix}_rank": self.rank,
            },
        )


class GameResult:
    """スコアデータ"""

    def __init__(self, **kwargs):
        # ゲーム結果
        self.ts: str = ""
        """タイムスタンプ"""
        self.p1: Score = Score()
        """東家成績"""
        self.p2: Score = Score()
        """南家成績"""
        self.p3: Score = Score()
        """西家成績"""
        self.p4: Score = Score()
        """北家成績"""
        self.comment: Optional[str] = None
        """ゲームコメント"""
        self.deposit: int = 0
        """供託"""

        # 付属情報
        self.rule_version: str = ""
        """ルールバージョン"""
        self.origin_point: int = 250
        """配給原点"""
        self.return_point: int = 300
        """返し点"""
        self.rank_point: list = [30, 10, -10, -30]
        """順位点"""
        self.draw_split: bool = False
        """同着時に順位点を山分けにするか"""
        self.source: Optional[str] = None
        """データ入力元識別子"""

        self.calc(**kwargs)

    def __bool__(self) -> bool:
        return all(self.to_list("name") + self.to_list("str"))

    def __eq__(self, other):
        if not isinstance(other, GameResult):
            return NotImplemented
        return all(
            [
                self.ts == other.ts,
                self.p1.name == other.p1.name,
                self.p1.rpoint == other.p1.rpoint,
                self.p2.name == other.p2.name,
                self.p2.rpoint == other.p2.rpoint,
                self.p3.name == other.p3.name,
                self.p3.rpoint == other.p3.rpoint,
                self.p4.name == other.p4.name,
                self.p4.rpoint == other.p4.rpoint,
                self.rule_version == other.rule_version,
                self.comment == other.comment,
                self.source == other.source,
            ]
        )

    def __lt__(self, other):
        if not isinstance(other, GameResult):
            return NotImplemented
        return self.ts < other.ts

    def has_valid_data(self) -> bool:
        """DB更新に必要なデータを持っているかチェック"""
        return all(
            [
                self.ts,
                isinstance(self.ts, str),
                self.p1.has_valid_data(),
                self.p2.has_valid_data(),
                self.p3.has_valid_data(),
                self.p4.has_valid_data(),
                all(self.to_list("rank")),
            ]
        )

    def set(self, **kwargs) -> None:
        """テータ取り込み"""
        for prefix in ("p1", "p2", "p3", "p4"):
            prefix_obj = cast(Score, getattr(self, prefix))
            if f"{prefix}_name" in kwargs:
                prefix_obj.name = str(kwargs[f"{prefix}_name"])
            if f"{prefix}_str" in kwargs:
                input_str = cast(str, kwargs[f"{prefix}_str"]).strip()
                input_str = re.sub(r"(-)+|(\+)+", r"\1\2", input_str)  # 連続した符号を集約
                input_str = re.sub(r"(-|\+)0+", r"\1", input_str)  # 符号の直後のゼロを削除
                if input_str != "0":  # 先頭のゼロとプラス記号を削除
                    input_str = re.sub(r"^[0+]+", "", input_str)
                prefix_obj.r_str = input_str
            if f"{prefix}_r_str" in kwargs:
                prefix_obj.r_str = kwargs[f"{prefix}_str"]
            if f"{prefix}_rpoint" in kwargs and isinstance(kwargs[f"{prefix}_rpoint"], int):
                prefix_obj.rpoint = int(kwargs[f"{prefix}_rpoint"])
            if f"{prefix}_point" in kwargs and isinstance(kwargs[f"{prefix}_point"], (float, int)):
                prefix_obj.point = float(kwargs[f"{prefix}_point"])
            if f"{prefix}_rank" in kwargs and isinstance(kwargs[f"{prefix}_rank"], int):
                prefix_obj.rank = int(kwargs[f"{prefix}_rank"])

        if "ts" in kwargs and isinstance(kwargs["ts"], str):
            self.ts = kwargs["ts"]
        if "rule_version" in kwargs and isinstance(kwargs["rule_version"], str):
            self.rule_version = str(kwargs["rule_version"])
        if "deposit" in kwargs and isinstance(kwargs["deposit"], int):
            self.deposit = int(kwargs["deposit"])
        if "origin_point" in kwargs and isinstance(kwargs["origin_point"], int):
            self.origin_point = int(kwargs["origin_point"])
        if "return_point" in kwargs and isinstance(kwargs["return_point"], int):
            self.return_point = int(kwargs["return_point"])
        if "rank_point" in kwargs and isinstance(kwargs["rank_point"], list):
            self.rank_point = kwargs["rank_point"]
        if "draw_split" in kwargs and isinstance(kwargs["draw_split"], bool):
            self.draw_split = kwargs["draw_split"]
        if "comment" in kwargs:
            self.comment = kwargs["comment"]
        if "source" in kwargs:
            self.source = kwargs["source"]

    def to_dict(self) -> "ScoreDict":
        """データを辞書で返す

        Returns:
            ScoreDict: スコアデータ
        """

        return {
            "ts": self.ts,
            **self.p1.to_dict("p1"),
            **self.p2.to_dict("p2"),
            **self.p3.to_dict("p3"),
            **self.p4.to_dict("p4"),
            "deposit": self.deposit,
            "comment": self.comment,
            "rule_version": self.rule_version,
            "source": self.source,
        }

    def to_text(self, kind: Literal["simple", "detail", "logging"] = "simple") -> str:
        """データをテキストで返す

        Args:
            kind (Literal, optional): 表示形式
                - *simple*: 簡易情報 (Default)
                - *detail*: 詳細情報
                - *logging*: ロギング用

        Returns:
            str: スコアデータ
        """

        ret_text: str = ""
        match kind:
            case "simple":
                ret_text += f"[{self.p1.name} {self.p1.r_str}] "
                ret_text += f"[{self.p2.name} {self.p2.r_str}] "
                ret_text += f"[{self.p3.name} {self.p3.r_str}] "
                ret_text += f"[{self.p4.name} {self.p4.r_str}] "
                ret_text += f"[供託 {self.deposit}] [{self.comment if self.comment else None}]"
            case "detail":
                ret_text += f"[{self.p1.rank}位 {self.p1.name} {self.p1.rpoint * 100}点 ({self.p1.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p2.rank}位 {self.p2.name} {self.p2.rpoint * 100}点 ({self.p2.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p3.rank}位 {self.p3.name} {self.p3.rpoint * 100}点 ({self.p3.point}pt)] ".replace("-", "▲")
                ret_text += f"[{self.p4.rank}位 {self.p4.name} {self.p4.rpoint * 100}点 ({self.p4.point}pt)] ".replace("-", "▲")
                ret_text += f"[供託 {self.deposit * 100}点] "
                ret_text += f"[{self.comment if self.comment else None}]"
            case "logging":
                ret_text += f"ts={self.ts}, deposit={self.deposit}, rule_version={self.rule_version}, "
                ret_text += f"p1={self.p1.to_dict('p1')}, p2={self.p2.to_dict('p2')}, p3={self.p3.to_dict('p3')}, p4={self.p4.to_dict('p4')}, "
                ret_text += f"comment={self.comment if self.comment else None}, source={self.source}"

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
            list[str | int | float]: リスト
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
            self.set(**self._calculation_point())

    def _calculation_point(self) -> dict:
        """獲得ポイントと順位を計算する

        Returns:
            dict: 更新用辞書(順位と獲得ポイントのデータ)
        """

        def normalized_expression(expr: str) -> int:
            """入力文字列を式として評価し、計算結果を返す

            Args:
                expr (str): 入力式

            Returns:
                int: 計算結果
            """

            normalized: list = []

            for token in re.findall(r"\d+|[+\-*/]", expr):
                if isinstance(token, str):
                    if token.isnumeric():
                        normalized.append(str(int(token)))
                    else:
                        normalized.append(token)

            return eval("".join(normalized))

        def point_split(point: list) -> list:
            """順位点を山分けする

            Args:
                point (list): 山分けするポイントのリスト

            Returns:
                list: 山分けした結果
            """

            new_point = [int(sum(point) / len(point))] * len(point)
            if sum(point) % len(point):
                new_point[0] += sum(point) % len(point)
                if sum(point) < 0:
                    new_point = list(map(lambda x: x - 1, new_point))

            return new_point

        # 計算用データフレーム
        score_df = pd.DataFrame({"rpoint": [normalized_expression(str(x)) for x in self.to_list("str")]}, index=["p1", "p2", "p3", "p4"])

        work_rank_point = self.rank_point.copy()  # ウマ
        work_rank_point[0] += int((self.return_point - self.origin_point) / 10 * 4)  # オカ

        if self.draw_split:  # 山分け
            score_df["rank"] = score_df["rpoint"].rank(ascending=False, method="min").astype("int")

            # 順位点リストの更新
            match "".join(score_df["rank"].sort_values().to_string(index=False).split()):
                case "1111":
                    work_rank_point = point_split(work_rank_point)
                case "1114":
                    new_point = point_split(work_rank_point[0:3])
                    work_rank_point[0] = new_point[0]
                    work_rank_point[1] = new_point[1]
                    work_rank_point[2] = new_point[2]
                case "1134":
                    new_point = point_split(work_rank_point[0:2])
                    work_rank_point[0] = new_point[0]
                    work_rank_point[1] = new_point[1]
                case "1133":
                    new_point = point_split(work_rank_point[0:2])
                    work_rank_point[0] = new_point[0]
                    work_rank_point[1] = new_point[1]
                    new_point = point_split(work_rank_point[2:4])
                    work_rank_point[2] = new_point[0]
                    work_rank_point[3] = new_point[1]
                case "1222":
                    new_point = point_split(work_rank_point[1:4])
                    work_rank_point[1] = new_point[0]
                    work_rank_point[2] = new_point[1]
                    work_rank_point[3] = new_point[2]
                case "1224":
                    new_point = point_split(work_rank_point[1:3])
                    work_rank_point[1] = new_point[0]
                    work_rank_point[2] = new_point[1]
                case "1233":
                    new_point = point_split(work_rank_point[2:4])
                    work_rank_point[2] = new_point[0]
                    work_rank_point[3] = new_point[1]
                case _:
                    pass

        else:  # 席順
            score_df["rank"] = score_df["rpoint"].rank(ascending=False, method="first").astype("int")

        # 獲得ポイントの計算 (素点-配給原点)/10+順位点
        score_df["position"] = score_df["rpoint"].rank(ascending=False, method="first").astype("int")  # 加算する順位点リストの位置
        score_df["point"] = (score_df["rpoint"] - self.return_point) / 10 + score_df["position"].apply(lambda p: work_rank_point[p - 1])
        score_df["point"] = score_df["point"].apply(lambda p: float(f"{p:.1f}"))  # 桁ブレ修正

        # 返却値用辞書
        ret_dict = {f"{k}_{x}": v for x in score_df.columns for k, v in score_df[x].to_dict().items()}
        ret_dict.update(deposit=int(self.origin_point * 4 - score_df["rpoint"].sum()))

        return ret_dict
