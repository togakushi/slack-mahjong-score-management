"""
libs/datamodels.py
"""

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Literal, Optional, Union, get_type_hints

from cls.timekit import ExtendedDatetime as ExtDt

if TYPE_CHECKING:
    import pandas as pd


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
        total_point: float = field(default=0.0)
        """通算ポイント"""
        avg_point: float = field(default=0.0)
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

        # 最大/最小
        rpoint_max: int = field(default=0)
        rpoint_min: int = field(default=0)
        point_max: float = field(default=0.0)
        point_min: float = field(default=0.0)

        # 収支データ
        score: int = field(default=0)
        score_rank1: int = field(default=0)
        score_rank2: int = field(default=0)
        score_rank3: int = field(default=0)
        score_rank4: int = field(default=0)

        # レコード
        top1_max: int = field(default=0)
        top1_cur: int = field(default=0)
        top2_max: int = field(default=0)
        top2_cur: int = field(default=0)
        top3_max: int = field(default=0)
        top3_cur: int = field(default=0)
        lose2_max: int = field(default=0)
        lose2_cur: int = field(default=0)
        lose3_max: int = field(default=0)
        lose3_cur: int = field(default=0)
        lose4_max: int = field(default=0)
        lose4_cur: int = field(default=0)

        # 集計範囲
        first_game: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
        """最初の記録時間"""
        last_game: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
        """最後の記録時間"""
        first_comment: Optional[str] = field(default=None)
        """最初の記録時間のコメント"""
        last_comment: Optional[str] = field(default=None)
        """最後の記録時間のコメント"""

        def avg_balance(self, pattern: str) -> float:
            """平均収支計算

            Args:
                pattern (str): 計算パターン

            Returns:
                float: 計算結果
            """

            ret: float = 0.0

            match pattern:
                case "rank1":
                    ret = round(self.score_rank1 * 100 / self.rank1, 1)
                case "rank2":
                    ret = round(self.score_rank2 * 100 / self.rank2, 1)
                case "rank3":
                    ret = round(self.score_rank3 * 100 / self.rank3, 1)
                case "rank4":
                    ret = round(self.score_rank4 * 100 / self.rank4, 1)
                case "top2":
                    ret = round((self.score_rank1 + self.score_rank2) * 100 / (self.rank1 + self.rank2), 1)
                case "lose2":
                    ret = round((self.score_rank3 + self.score_rank4) * 100 / (self.rank3 + self.rank4), 1)
                case _:
                    ret = round(self.score * 100 / self.count, 1)

            return ret

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

        def update_from_dict(self, data: dict) -> None:
            """辞書から値を更新

            Args:
                data (dict): 更新データ（キーはフィールド名）
            """
            type_hints = get_type_hints(self.__class__)
            for field_obj in fields(self):
                if field_obj.name not in data:
                    continue

                value = data[field_obj.name]
                if value is None:
                    setattr(self, field_obj.name, None)
                    continue

                field_type = type_hints.get(field_obj.name, type(None))

                # 型別の変換処理
                if field_type in (int, float, str, bool):
                    setattr(self, field_obj.name, field_type(value))
                elif field_type is ExtDt or (hasattr(field_type, "__origin__") and field_type.__origin__ is Union):
                    # ExtDtまたはOptional型
                    if hasattr(field_type, "__args__"):
                        # Optional[X]の場合、Xの型を取得
                        inner_type = next(arg for arg in field_type.__args__ if arg is not type(None))
                        setattr(self, field_obj.name, inner_type(value) if value is not None else None)
                    else:
                        setattr(self, field_obj.name, ExtDt(value))
                else:
                    setattr(self, field_obj.name, value)

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
    mode: Literal[3, 4] = field(default=4)
    """集計モード"""
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

        for idx, data in df.to_dict(orient="index").items():
            seat_map = {0: self.seat0, 1: self.seat1, 2: self.seat2, 3: self.seat3, 4: self.seat4}
            if idx in seat_map:
                seat_map[idx].update_from_dict(data)

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

    def rank_distr_list(self) -> list:
        """座席別順位分布

        Returns:
            list: _description_
        """

        return [
            self.seat1.rank_distr,
            self.seat2.rank_distr,
            self.seat3.rank_distr,
            self.seat4.rank_distr,
        ][: self.mode]

    def rank_distr_list2(self) -> list:
        """座席別順位分布

        Returns:
            list: _description_
        """

        return [
            self.seat1.rank_distr2,
            self.seat2.rank_distr2,
            self.seat3.rank_distr2,
            self.seat4.rank_distr2,
        ][: self.mode]
