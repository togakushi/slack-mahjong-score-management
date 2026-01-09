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

    >>> ExtendedDatetime.range("今月").format("ymdhm")
    ['2025/04/01 00:00', '2025/04/30 23:59']

    >>> ExtendedDatetime.range("今月").dict_format("ymd", "ja")
    {'start': '2025年04月01日', 'end': '2025年04月30日'}

    >>> ExtendedDatetime("2025-01-01 01:23:45", hours=-12).range("今年")
    [2024-01-01 00:00:00.000000, 2024-12-31 23:59:59.999999]
"""

from datetime import datetime
from enum import StrEnum
from functools import total_ordering
from typing import Callable, List, Optional, TypeAlias, TypedDict, Union, cast

from dateutil.relativedelta import MO, SU, relativedelta


class Format(StrEnum):
    """フォーマット変換で指定する種類"""

    TS = "ts"
    """タイムスタンプ"""
    Y = "y"
    """年(%Y)"""
    YM = "ym"
    """年月(%Y/%m)"""
    YMD = "ymd"
    """年月日(%Y/%m/%d)"""
    YMDHM = "ymdhm"
    """年月日時分(%Y/%m/%d %H:%M)"""
    YMDHMS = "ymdhms"
    """年月日時分秒(%Y/%m/%d %H:%M:%S)"""
    HM = "hm"
    """時分(%H:%M)"""
    HMS = "hms"
    """時分秒(%H:%M:%S)"""
    SQL = "sql"
    """SQLite用フォーマット(%Y-%m-%d %H:%M:%S.%f)"""
    EXT = "ext"
    """ファイル拡張子用(%Y%m%d-%H%M%S)"""
    JY_O = "jy_o"
    JYM_O = "jym_o"
    YMD_O = "ymd_o"


class Delimiter(StrEnum):
    """区切り記号"""

    SLASH = "slash"
    """スラッシュ(ex: %Y/%m/%d)"""
    HYPHEN = "hyphen"
    """ハイフン(ex: %Y-%m-%d)"""
    NUMBER = "number"
    """区切り無し (ex: %Y%m%d)"""
    JAPANESE = "japanese"
    """Japanese Style (ex: %Y%年m%月d日)"""
    UNDEFINED = ""
    """未定義"""


class DateRangeSpec(TypedDict):
    """日付範囲変換キーワード用辞書"""

    keyword: list[str]
    range: Callable[[datetime], list[datetime]]


DATE_RANGE_MAP: dict[str, DateRangeSpec] = {
    "today": {
        "keyword": ["今日", "本日", "当日"],
        "range": lambda x: [
            x.replace(hour=0, minute=0, second=0, microsecond=0),
            x.replace(hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "yesterday": {
        "keyword": ["昨日"],
        "range": lambda x: [
            x + relativedelta(days=-1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(days=-1, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "this_week": {
        "keyword": ["今週"],
        "range": lambda x: [
            x + relativedelta(weekday=MO(-1), hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(weekday=SU, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "last_week": {
        "keyword": ["先週"],
        "range": lambda x: [
            x + relativedelta(weekday=MO(-2), hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(weekday=SU(-1), hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "this_month": {
        "keyword": ["今月"],
        "range": lambda x: [
            x + relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "last_month": {
        "keyword": ["先月", "昨月"],
        "range": lambda x: [
            x + relativedelta(months=-1, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(months=-1, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "two_months_ago": {
        "keyword": ["先々月"],
        "range": lambda x: [
            x + relativedelta(months=-2, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(months=-2, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "this_year": {
        "keyword": ["今年"],
        "range": lambda x: [
            x + relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "last_year": {
        "keyword": ["去年", "昨年"],
        "range": lambda x: [
            x + relativedelta(years=-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(years=-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "year_before_last": {
        "keyword": ["一昨年"],
        "range": lambda x: [
            x + relativedelta(years=-2, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(years=-2, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "first_day": {
        "keyword": ["最初"],
        "range": lambda x: [
            x + relativedelta(year=1900, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
        ],
    },
    "last_day": {
        "keyword": ["最後"],
        "range": lambda x: [
            x + relativedelta(days=1, hour=23, minute=59, second=59, microsecond=999999),
        ],
    },
    "all": {
        "keyword": ["全部"],
        "range": lambda x: [
            x + relativedelta(year=1900, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            x + relativedelta(days=1, hour=23, minute=59, second=59, microsecond=999999),
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

    def __init__(self, value: Optional[AcceptedType] = None, **relativedelta_kwargs):
        """ExtendedDatetimeの初期化

        Args:
            value (Optional[AcceptedType], optional): 引数. Defaults to None.
                - None: 現在時刻(`datetime.now()`)で初期化
            relativedelta_kwargs (dict): 初期化時にrelativedelta()に渡す引数
        """

        self._dt = self.convert(value) if value else datetime.now()
        if relativedelta_kwargs:
            self._dt += relativedelta(**relativedelta_kwargs)

    def __str__(self) -> str:
        return self.format(Format.SQL)

    def __repr__(self) -> str:
        return self.format(Format.SQL)

    def __eq__(self, other):
        if isinstance(other, ExtendedDatetime):
            return self.dt == other.dt
        if isinstance(other, datetime):
            return self.dt == other
        if isinstance(other, str):
            return self.format(Format.SQL) == other
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

    @dt.setter
    def dt(self, value: AcceptedType) -> None:
        """dtに対するsetter"""
        self._dt = self.convert(value)

    def set(self, value: AcceptedType) -> None:
        """渡された値をdatetime型に変換して保持

        Args:
            value (AcceptedType): 入力値
        """

        self._dt = self.convert(value)

    def format(self, fmt: Format, delimiter: Delimiter = Delimiter.UNDEFINED) -> str:
        """フォーマット変換

        Args:
            fmt (Format): 変換形式
            delimiter (Delimiter): 区切り

        Raises:
            ValueError: 受け付けない変換形式

        Returns:
            str: 変換文字列
        """

        ret: str
        match fmt:
            case Format.TS:
                ret = str(self._dt.timestamp())
            case Format.Y | Format.JY_O:
                match delimiter:
                    case Delimiter.JAPANESE:
                        ret = self._dt.strftime("%Y年")
                    case _:
                        ret = self._dt.strftime("%Y")
            case Format.YM | Format.JYM_O:
                match delimiter:
                    case Delimiter.SLASH:
                        ret = self._dt.strftime("%Y/%m")
                    case Delimiter.HYPHEN:
                        ret = self._dt.strftime("%Y-%m")
                    case Delimiter.JAPANESE:
                        ret = self._dt.strftime("%Y年%m月")
                    case Delimiter.NUMBER:
                        ret = self._dt.strftime("%Y%m")
                    case _:
                        ret = self._dt.strftime("%Y/%m")
            case Format.YMD | Format.JYM_O:
                match delimiter:
                    case Delimiter.SLASH:
                        ret = self._dt.strftime("%Y/%m/%d")
                    case Delimiter.HYPHEN:
                        ret = self._dt.strftime("%Y-%m-%d")
                    case Delimiter.JAPANESE:
                        ret = self._dt.strftime("%Y年%m月%d日")
                    case Delimiter.NUMBER:
                        ret = self._dt.strftime("%Y%m%d")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d")
            case Format.YMDHM:
                match delimiter:
                    case Delimiter.SLASH:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
                    case Delimiter.HYPHEN:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M")
                    case Delimiter.JAPANESE:
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分")
                    case Delimiter.NUMBER:
                        ret = self._dt.strftime("%Y%m%d%H%M")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
            case Format.YMDHMS:
                match delimiter:
                    case Delimiter.SLASH:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
                    case Delimiter.HYPHEN:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S")
                    case Delimiter.JAPANESE:
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分%S秒")
                    case Delimiter.NUMBER:
                        ret = self._dt.strftime("%Y%m%d%H%M%S")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
            case Format.SQL:
                match delimiter:
                    case Delimiter.SLASH:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S.%f")
                    case Delimiter.HYPHEN:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                    case Delimiter.NUMBER:
                        ret = self._dt.strftime("%Y%m%d%H%M%S%f")
                    case _:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            case Format.EXT:
                ret = self._dt.strftime("%Y%m%d-%H%M%S")
            case _:
                raise ValueError(f"Unknown format: {fmt}")

        return ret

    def range(self, value: str | list) -> "ExtendedDatetimeList":
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
            check_list = sum([str(x).split() for x in value], [])  # 平坦化

        ret: list[datetime] = []
        for word in check_list:
            for _, range_map in DATE_RANGE_MAP.items():
                if word in cast(list, range_map["keyword"]):
                    ret.extend(range_map["range"](self._dt))
                    break
            else:
                try:
                    try_time = self.convert(str(word))
                    ret.append(try_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    ret.append(try_time.replace(hour=23, minute=59, second=59, microsecond=999999))
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

        return ret

    @classmethod
    def print_range(cls) -> str:
        """指定可能キーワードで取得できる範囲の一覧

        Returns:
            str: 出力メッセージ
        """

        base_instance = cls()
        ret: str = ""

        for _, val in DATE_RANGE_MAP.items():
            for label in val["keyword"]:
                scope = " ～ ".join(base_instance.range(label).format(Format.YMD))
                ret += f"{label}：{scope}\n"

        return ret.strip()

    @staticmethod
    def convert(value: AcceptedType) -> datetime:
        """引数の型を判定してdatetimeへ変換

        Args:
            value (AcceptedType): 変換対象

        Raises:
            TypeError: str型が変換できない場合

        Returns:
            datetime: 変換した型
        """

        if isinstance(value, ExtendedDatetime):
            return value.dt
        if isinstance(value, datetime):
            return value
        if isinstance(value, float):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%Y/%m/%d %H:%M")

        raise TypeError("Unsupported type for datetime conversion")


class ExtendedDatetimeList(list):
    """ExtendedDatetimeを要素とする日付リストを扱う補助クラス"""

    Delimiter: TypeAlias = Delimiter

    def __add__(self, other):
        if isinstance(other, dict):
            return ExtendedDatetimeList([dt + other for dt in self])
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, dict):
            return ExtendedDatetimeList([dt - other for dt in self])
        return NotImplemented

    @property
    def start(self) -> ExtendedDatetime | None:
        """最小日付を返す。空ならNone。"""
        return min(self) if self else None

    @property
    def end(self) -> ExtendedDatetime | None:
        """最大日付を返す。空ならNone。"""
        return max(self) if self else None

    @property
    def period(self) -> List[ExtendedDatetime | None]:
        """最小値と最大値をリストで返す"""
        min_dt = min(self) if self else None
        max_dt = max(self) if self else None

        return [min_dt, max_dt]

    def format(self, fmt: Format = Format.SQL, delimiter: Delimiter = Delimiter.UNDEFINED) -> list[str]:
        """全要素にformatを適用した文字列リストを返す

        Args:
            fmt (Format, optional): フォーマット変換. Defaults to "sql".
            delimiter (Delimiter, optional): 区切り記号指定. Defaults to None.

        Returns:
            list[str]: 生成したリスト
        """

        return [dt.format(fmt, delimiter) for dt in self if isinstance(dt, ExtendedDatetime)]

    def dict_format(self, fmt: Format = Format.SQL, delimiter: Delimiter = Delimiter.UNDEFINED) -> dict[str, str]:
        """全要素にformatを適用し、最小日付と最大日付を辞書で返す

        Args:
            fmt (Format, optional): フォーマット変換. Defaults to "sql".
            delimiter (Delimiter, optional): 区切り記号指定. Defaults to None.

        Returns:
            dict[str, str]: 生成した辞書
        """

        date_range = [dt for dt in self if isinstance(dt, ExtendedDatetime)]

        if not date_range:
            return {}

        return {"start": min(date_range).format(fmt, delimiter), "end": max(date_range).format(fmt, delimiter)}
