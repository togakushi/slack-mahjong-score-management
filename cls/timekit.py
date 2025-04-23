"""
timekit - datetime 拡張ユーティリティ

- `ExtendedDatetime`: 柔軟な初期化と書式変換ができる datetime 拡張クラス
- `ExtendedDatetimeList`: ExtendedDatetimeを要素とする日付リストを扱う補助クラス

Examples:
    >>> from cls.timekit import ExtendedDatetime
    >>> t = ExtendedDatetime("2025-04-19 12:34:56")
    >>> t.format("ymdhm")
    '2025/04/19 12:34'

    >>> t.set("2025-05-01 00:00:00")
    >>> t.format("sql")
    '2025-05-01 00:00:00.000000'

    >>> from dateutil.relativedelta import relativedelta
    >>> t2 = t + relativedelta(days=93)
    >>> t2.format("ymd")
    '2025/08/02'

    >>> t + {"days": 1, "months": 2}
    2025-07-02 00:00:00.000000

    >>> ExtendedDatetime.get_range("今月").format("ymdhm")
    ['2025/04/01 00:00', '2025/04/30 23:59']

    >>> ExtendedDatetime.get_range("今月").dict_format("ymd", "ja")
    {'start': '2025年04月01日', 'end': '2025年04月30日'}
"""

from collections.abc import Callable
from datetime import datetime
from functools import total_ordering
from typing import Literal, TypeAlias, Union, cast

from dateutil.relativedelta import relativedelta

from cls.types import DateRangeSpec
from libs.data import lookup

FormatType: TypeAlias = Literal[
    "ts", "y", "ym", "ymd", "ymdhm", "ymdhms", "hm", "hms", "sql", "ext",
]
"""フォーマット変換で指定する種類
- **ts**: タイムスタンプ
- **y**: %Y
- **ym**: %Y/%m
- **ymd**: %Y/%m/%d
- **ymdhm**: %Y/%m/%d %H:%M
- **ymdhms**: %Y/%m/%d %H:%M:%S
- **hm**: %H:%M:%S
- **hms**: %H:%M
- **sql**: SQLite用フォーマット(%Y-%m-%d %H:%M:%S.%f)
- **ext**: ファイル拡張子用(%Y%m%d-%H%M%S)
"""

DelimiterStyle: TypeAlias = Literal[
    "slash", "/", "hyphen", "-", "ja", "number", "num", None
]
"""区切り記号
- **slash** | **/**: スラッシュ(ex: %Y/%m/%d)
- **hyphen** | **-**: ハイフン(ex: %Y-%m-%d)
- **number** | **num**: 無し (ex: %Y%m%d)
- **ja**: Japanese Style (ex: %Y%年m%月d日)
- **None**: 未指定
"""

DATE_RANGE_MAP: dict[str, DateRangeSpec] = {
    "appointed": {
        "keyword": ["当日"],
        "range": lambda: [
            (datetime.now() + relativedelta(hours=-12)).replace(hour=12, minute=0, second=0, microsecond=0),
        ],
    },
    "today": {
        "keyword": ["今日", "本日"],
        "range": lambda: [
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        ],
    },
    "yesterday": {
        "keyword": ["昨日"],
        "range": lambda: [
            datetime.now() + relativedelta(days=-1, hour=0, minute=0, second=0, microsecond=0),
        ],
    },
    "this_month": {
        "keyword": ["今月"],
        "range": lambda: [
            datetime.now() + relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "last_month": {
        "keyword": ["先月", "昨月"],
        "range": lambda: [
            datetime.now() + relativedelta(months=-1, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(months=-1, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "two_months_ago": {
        "keyword": ["先々月"],
        "range": lambda: [
            datetime.now() + relativedelta(months=-2, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(months=-2, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "this_year": {
        "keyword": ["今年"],
        "range": lambda: [
            datetime.now() + relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "last_year": {
        "keyword": ["去年", "昨年"],
        "range": lambda: [
            datetime.now() + relativedelta(years=-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(years=-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "year_before_last": {
        "keyword": ["一昨年"],
        "range": lambda: [
            datetime.now() + relativedelta(years=-2, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.now() + relativedelta(years=-2, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "first_day": {
        "keyword": ["最初"],
        "range": lambda: [
            lookup.db.first_record() + relativedelta(days=-1),
        ],
    },
    "last_day": {
        "keyword": ["最後"],
        "range": lambda: [
            datetime.now() + relativedelta(days=1, hour=23, minute=59, second=59, microsecond=999999)
        ],
    },
    "all": {
        "keyword": ["全部"],
        "range": lambda: [
            lookup.db.first_record() + relativedelta(days=-1),
            datetime.now() + relativedelta(days=1, hour=23, minute=59, second=59, microsecond=999999)
        ],
    },
}
"""キーワードと日付範囲のマッピングリスト"""


@total_ordering
class ExtendedDatetime:
    """datetime拡張クラス"""

    _dt: datetime
    """操作対象"""

    # 型アノテーション用定数
    AcceptedType: TypeAlias = Union[str, float, datetime, "ExtendedDatetime"]
    """引数として受け付ける型
    - **str**: 日付文字列（ISO形式など）
    - **float**: UNIXタイムスタンプ
    - **datetime** / **ExtendedDatetime**: オブジェクトをそのまま利用
    """

    FormatType: TypeAlias = FormatType
    DelimiterStyle: TypeAlias = DelimiterStyle

    _range_map: dict[str, Callable[[], list[datetime]]] = {}
    """範囲指定キーワードマップ"""

    def __init__(self, value: AcceptedType | None = None):
        """ExtendedDatetimeの初期化

        Args:
            value (`AcceptedType` | None, optional): 引数
               - None: 現在時刻(`datetime.now()`)で初期化
        """

        self._dt = self.convert(value) if value else datetime.now()

    def __str__(self) -> str:
        return self.format("sql")

    def __repr__(self) -> str:
        return self.format("sql")

    def __eq__(self, other):
        if isinstance(other, ExtendedDatetime):
            return self.dt == other.dt
        if isinstance(other, datetime):
            return self.dt == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, ExtendedDatetime):
            return self.dt < other.dt
        if isinstance(other, datetime):
            return self.dt < other
        return NotImplemented

    def __add__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        if isinstance(other, dict):
            delta = relativedelta(**other)
        elif isinstance(other, relativedelta):
            delta = other
        else:
            raise TypeError("Expected dict or relativedelta")

        return ExtendedDatetime(self._dt + delta)

    def __sub__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        if isinstance(other, dict):
            delta = relativedelta(**other)
        elif isinstance(other, relativedelta):
            delta = other
        else:
            raise TypeError("Expected dict or relativedelta")

        return ExtendedDatetime(self._dt - delta)

    def __radd__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        return self.__add__(other)

    def __rsub__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        return self.__sub__(other)

    def __hash__(self):
        return hash(self.dt)

    def __getattr__(self, name):
        return getattr(self._dt, name)

    @property
    def dt(self) -> datetime:
        """datetime型を返すプロパティ"""
        return self._dt

    def set(self, value: AcceptedType) -> None:
        """渡された値をdatetime型に変換して保持

        Args:
            value (`AcceptedType`): 入力値
        """

        self._dt = self.convert(value)

    def format(self, fmt: FormatType, delimiter: DelimiterStyle = None) -> str:
        """フォーマット変換

        Args:
            fmt (`FormatType`): 変換形式
            delimiter (`DelimiterStyle`): 区切り

        Raises:
            ValueError: 受け付けない変換形式

        Returns:
            str: 変換文字列
        """

        ret: str
        match fmt:
            case "ts":
                ret = str(self._dt.timestamp())
            case "y":
                match delimiter:
                    case "ja":
                        ret = self._dt.strftime("%Y年")
                    case _:
                        ret = self._dt.strftime("%Y")
            case "ym":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m")
                    case _:
                        ret = self._dt.strftime("%Y/%m")
            case "ymd":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d")
            case "ymdhm":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
            case "ymdhms":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分%S秒")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M%S")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
            case "sql":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S.%f")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M%S%f")
                    case _:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            case "ext":
                ret = self._dt.strftime("%Y%m%d-%H%M%S")
            case _:
                raise ValueError(f"Unknown format: {fmt}")

        return (ret)

    @classmethod
    def range(cls, value: str | list) -> "ExtendedDatetimeList":
        """キーワードが示す範囲をリストで返す

        Args:
            value (str | list): 範囲取得キーワード
                - str: スペース区切りで分割してリスト化
                - list: スペース区切りで再分割

        Returns:
            ExtendedDatetimeList: 日付リスト
        """

        if isinstance(value, str):
            check_list = value.split()
        else:
            check_list = sum([x.split() for x in value], [])  # 平坦化

        ret: list[datetime] = []
        for word in check_list:
            for _, range_map in DATE_RANGE_MAP.items():
                if word in cast(list, range_map["keyword"]):
                    ret.extend(range_map["range"]())
                    break
            else:
                try:
                    ret.append(cls.convert(str(word)))
                except ValueError:
                    pass

            continue

        return ExtendedDatetimeList([ExtendedDatetime(x) for x in ret])

    @classmethod
    def valid_keywords(cls) -> list[str]:
        """有効なキーワード一覧

        Returns:
            list[str]: キーワード一覧
        """

        ret: list = []
        for _, range_map in DATE_RANGE_MAP.items():
            ret.extend(cast(list, range_map["keyword"]))

        return (ret)

    @staticmethod
    def convert(value: AcceptedType) -> datetime:
        """引数の型を判定してdatetimeへ変換

        Args:
            value (`AcceptedType`): 変換対象

        Raises:
            TypeError: str型が変換できない場合

        Returns:
            datetime: 変換した型
        """

        if isinstance(value, ExtendedDatetime):
            return value.dt
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, float):
            return datetime.fromtimestamp(value)
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%Y/%m/%d %H:%M")
        else:
            raise TypeError("Unsupported type for datetime conversion")


class ExtendedDatetimeList(list):
    """ExtendedDatetimeを要素とする日付リストを扱う補助クラス"""

    FormatType: TypeAlias = FormatType
    DelimiterStyle: TypeAlias = DelimiterStyle

    @property
    def start(self) -> ExtendedDatetime | None:
        """最小日付を返す。空ならNone。"""
        return (min(self) if self else None)

    @property
    def end(self) -> ExtendedDatetime | None:
        """最大日付を返す。空ならNone。"""
        return (max(self) if self else None)

    def format(self, fmt: FormatType = "sql", delimiter: DelimiterStyle = None) -> list[str]:
        """全要素にformatを適用した文字列リストを返す

        Args:
            fmt (`FormatType`, optional): フォーマット変換. Defaults to "sql".
            delimiter (`DelimiterStyle`, optional): 区切り記号指定. Defaults to None.

        Returns:
            list[str]: 生成したリスト
        """

        return [dt.format(fmt, delimiter) for dt in self if isinstance(dt, ExtendedDatetime)]

    def dict_format(self, fmt: FormatType = "sql", delimiter: DelimiterStyle = None) -> dict[str, str]:
        """全要素にformatを適用し、最小日付と最大日付を辞書で返す

        Args:
            fmt (`FormatType`, optional): フォーマット変換. Defaults to "sql".
            delimiter (`DelimiterStyle`, optional): 区切り記号指定. Defaults to None.

        Returns:
            dict[str, str]: 生成した辞書
        """

        date_range = [dt.format(fmt, delimiter) for dt in self if isinstance(dt, ExtendedDatetime)]

        if not date_range:
            return ({})

        return ({"start": min(date_range), "end": max(date_range)})
