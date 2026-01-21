"""
cls/result.py
"""

import textwrap
from dataclasses import dataclass, field, fields
from typing import Literal, Optional, Union, get_type_hints

import pandas as pd

from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import loader


@dataclass
class StatsDetailed:
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
                if self.rank1:
                    ret = round(self.score_rank1 * 100 / self.rank1, 1)
            case "rank2":
                if self.rank2:
                    ret = round(self.score_rank2 * 100 / self.rank2, 1)
            case "rank3":
                if self.rank3:
                    ret = round(self.score_rank3 * 100 / self.rank3, 1)
            case "rank4":
                if self.rank4:
                    ret = round(self.score_rank4 * 100 / self.rank4, 1)
            case "top2":
                if self.rank1 + self.rank2:
                    ret = round((self.score_rank1 + self.score_rank2) * 100 / (self.rank1 + self.rank2), 1)
            case "lose2":
                if self.rank3 + self.rank4:
                    ret = round((self.score_rank3 + self.score_rank4) * 100 / (self.rank3 + self.rank4), 1)
            case _:
                if self.count:
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
        if self.count:
            return round(self.rank1 / self.count, 4)
        return 0.0

    @property
    def rank2_rate(self) -> float:
        if self.count:
            return round(self.rank2 / self.count, 4)
        return 0.0

    @property
    def rank3_rate(self) -> float:
        if self.count:
            return round(self.rank3 / self.count, 4)
        return 0.0

    @property
    def rank4_rate(self) -> float:
        if self.count:
            return round(self.rank4 / self.count, 4)
        return 0.0

    @property
    def flying_rate(self) -> float:
        if self.count:
            return round(self.flying / self.count, 4)
        return 0.0

    @property
    def yakuman_rate(self) -> float:
        if self.count:
            return round(self.yakuman / self.count, 4)
        return 0.0

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

    def war_record(self) -> str:
        return f"{self.count} 戦 ({self.win} 勝 {self.lose} 敗 {self.draw} 分)"

    def best_record(self) -> str:
        rpoint_max = f"{self.rpoint_max * 100:+}点".replace("-", "▲") if self.rpoint_max else "記録なし"
        point_max = f"{self.point_max:+.1f}pt".replace("-", "▲") if self.point_max else "記録なし"

        ret = textwrap.dedent(f"""\
            連続トップ：{self._work(self.top1_cur, self.top1_max)}
            連続連対：{self._work(self.top2_cur, self.top2_max)}
            連続ラス回避：{self._work(self.top3_cur, self.top3_max)}
            最大素点：{rpoint_max}
            最大獲得ポイント：{point_max}
            """)
        return ret.strip()

    def worst_record(self) -> str:
        rpoint_min = f"{self.rpoint_min * 100:+}点".replace("-", "▲") if self.rpoint_min else "記録なし"
        point_min = f"{self.point_min:+.1f}pt".replace("-", "▲") if self.point_min else "記録なし"

        ret = textwrap.dedent(f"""\
            連続ラス：{self._work(self.lose4_cur, self.lose4_max)}
            連続逆連対：{self._work(self.lose3_cur, self.lose3_max)}
            連続トップなし：{self._work(self.lose2_cur, self.lose2_max)}
            最大素点：{rpoint_min}
            最大獲得ポイント：{point_min}
            """)
        return ret.strip()

    def _work(self, c_num: int, m_num: int) -> str:
        """単位設定

        Args:
            c_num (int): 現在値
            m_num (int): 最大値

        Returns:
            str: 生成文字列
        """

        c_str = f"{c_num} 回目" if c_num else f"{c_num} 回"
        if m_num:
            m_str = "最大 1 回" if m_num == 1 else f"最大 {m_num} 連続"
            if m_num == c_num:
                m_str = "記録更新中"
        else:
            m_str = "記録なし"

        return f"{c_str} ({m_str})"


@dataclass
class StatsInfo:
    """成績情報"""

    name: str = field(default="")
    """プレイヤー名/チーム名"""

    # 統計データ
    seat0: StatsDetailed = field(default_factory=StatsDetailed)
    """全席"""
    seat1: StatsDetailed = field(default_factory=StatsDetailed)
    """東家"""
    seat2: StatsDetailed = field(default_factory=StatsDetailed)
    """南家"""
    seat3: StatsDetailed = field(default_factory=StatsDetailed)
    """西家"""
    seat4: StatsDetailed = field(default_factory=StatsDetailed)
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

    # 取り込みデータ
    result_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    record_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    def read(self, params: dict):
        """データ読み込み

        Args:
            params (dict): プレースホルダ
        """

        self.result_df = loader.read_data("RESULTS_INFO", params)
        self.record_df = loader.read_data("RECORD_INFO", params)

        if self.result_df.empty or self.record_df.empty:
            return

        self.set_parameter(**params)
        self.set_data(self.result_df)
        self.set_data(self.record_df)

    def set_data(self, df: "pd.DataFrame"):
        """集計結果取り込み

        Args:
            df (pd.DataFrame): 集計結果
        """

        seat_map = {0: self.seat0, 1: self.seat1, 2: self.seat2, 3: self.seat3, 4: self.seat4}

        for _, row in df.iterrows():
            if "id" in df.columns:
                seat_id = row["id"]
                if isinstance(seat_id, int) and seat_id in seat_map:
                    seat_map[seat_id].update_from_dict(row.to_dict())

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
                raise ValueError(f"Unsupported mode: {kwargs['mode']}")

        if "rule_set" in kwargs and isinstance(kwargs["rule_set"], dict):
            self.rule_version = list(kwargs["rule_set"].values())
        if "player_name" in kwargs and isinstance(kwargs["player_name"], str):
            self.name = kwargs["player_name"]
        if "starttime" in kwargs and isinstance(kwargs["starttime"], (ExtDt, str)):
            self.starttime = ExtDt(kwargs["starttime"])
        if "endtime" in kwargs and isinstance(kwargs["endtime"], (ExtDt, str)):
            self.endtime = ExtDt(kwargs["endtime"])
        if "search_word" in kwargs and isinstance(kwargs["search_word"], str):
            self.search_word = kwargs["search_word"]

    @property
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

    @property
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

    @property
    def rank_avg_list(self) -> list:
        return [
            self.seat1.rank_avg,
            self.seat2.rank_avg,
            self.seat3.rank_avg,
            self.seat4.rank_avg,
        ][: self.mode]

    @property
    def flying_list(self) -> list:
        return [
            self.seat1.flying,
            self.seat2.flying,
            self.seat3.flying,
            self.seat4.flying,
        ][: self.mode]

    @property
    def yakuman_list(self) -> list:
        return [
            self.seat1.yakuman,
            self.seat2.yakuman,
            self.seat3.yakuman,
            self.seat4.yakuman,
        ][: self.mode]

    @property
    def summary(self) -> pd.DataFrame:
        ret_df = pd.DataFrame(
            {
                "count": [self.seat0.count],
                "war_record": [f"{self.seat0.win}-{self.seat0.lose}-{self.seat0.draw}"],
                "rank_avg": [self.seat0.rank_avg],
                "total_point": [f"{self.seat0.total_point:+.1f}pt".replace("-", "▲")],
                "avg_point": [f"{self.seat0.avg_point:+.1f}pt".replace("-", "▲")],
                "top2_rate-count": [f"{(self.seat0.rank1 + self.seat0.rank2) / self.seat0.count:.2%}({self.seat0.rank1 + self.seat0.rank2})"],
                "top3_rate-count": [
                    f"{(self.seat0.rank1 + self.seat0.rank2 + self.seat0.rank3) / self.seat0.count:.2%}"
                    + f"({self.seat0.rank1 + self.seat0.rank2 + self.seat0.rank3})",
                ],
                "rank1_rate-count": [f"{self.seat0.rank1_rate:.2%}({self.seat0.rank1})"],
                "rank2_rate-count": [f"{self.seat0.rank2_rate:.2%}({self.seat0.rank2})"],
                "rank3_rate-count": [f"{self.seat0.rank3_rate:.2%}({self.seat0.rank3})"],
                "rank4_rate-count": [f"{self.seat0.rank4_rate:.2%}({self.seat0.rank4})"],
                "flying_rate-count": [f"{self.seat0.flying_rate:.2%}({self.seat0.flying})"],
                "yakuman_rate-count": [f"{self.seat0.yakuman_rate:.2%}({self.seat0.yakuman})"],
                "avg_balance": [f"{self.seat0.avg_balance('all'):+.1f}点".replace("-", "▲")],
                "top2_balance": [f"{self.seat0.avg_balance('top2'):+.1f}点".replace("-", "▲")],
                "lose2_balance": [f"{self.seat0.avg_balance('lose2'):+.1f}点".replace("-", "▲")],
                "rank1_balance": [f"{self.seat0.avg_balance('rank1'):+.1f}点".replace("-", "▲")],
                "rank2_balance": [f"{self.seat0.avg_balance('rank2'):+.1f}点".replace("-", "▲")],
                "rank3_balance": [f"{self.seat0.avg_balance('rank3'):+.1f}点".replace("-", "▲")],
                "rank4_balance": [f"{self.seat0.avg_balance('rank4'):+.1f}点".replace("-", "▲")],
                "top1_max": [f"{self.seat0.top1_max}連続"],
                "top2_max": [f"{self.seat0.top2_max}連続"],
                "top3_max": [f"{self.seat0.top3_max}連続"],
                "lose2_max": [f"{self.seat0.lose2_max}連続"],
                "lose3_max": [f"{self.seat0.lose3_max}連続"],
                "lose4_max": [f"{self.seat0.lose4_max}連続"],
                "rpoint_max": [f"{self.seat0.rpoint_max * 100}点".replace("-", "▲")],
                "point_max": [f"{self.seat0.point_max:+.1f}pt".replace("-", "▲")],
                "rpoint_min": [f"{self.seat0.rpoint_min * 100}点".replace("-", "▲")],
                "point_min": [f"{self.seat0.point_min:+.1f}pt".replace("-", "▲")],
            },
            index=[self.name],
        )

        return ret_df
