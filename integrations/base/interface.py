"""
integrations/base/interface.py
"""

import re
from abc import ABC, abstractmethod
from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from typing import Any, Generic, Literal, Type, TypeVar, Union

from integrations.protocols import (MessageParserProtocol, MsgData, PostData,
                                    StatusData)

ConfigType = TypeVar("ConfigType", bound="IntegrationsConfig")
APIType = TypeVar("APIType", bound="APIInterface")
FunctionsType = TypeVar("FunctionsType", bound="FunctionsInterface")
ParserType = TypeVar("ParserType", bound="MessageParserInterface")


class AdapterInterface(ABC, Generic[ConfigType, APIType, FunctionsType, ParserType]):
    """アダプタインターフェース"""

    interface_type: str
    """サービス識別子"""

    conf: ConfigType
    """個別設定データクラス"""
    api: APIType
    """インターフェース操作APIインスタンス"""
    functions: FunctionsType
    """サービス専用関数インスタンス"""
    parser: Type[ParserType]
    """メッセージパーサクラス"""


@dataclass
class IntegrationsConfig(ABC):
    """個別設定値"""

    config_file: ConfigParser | None = field(default=None)
    """設定ファイル"""

    # 共通設定
    slash_command: str = field(default="")
    """スラッシュコマンド名"""

    badge_degree: bool = field(default=False)
    """プレイしたゲーム数に対して表示される称号
    - **True**: 表示する
    - **False**: 表示しない
    """
    badge_status: bool = field(default=False)
    """勝率に対して付く調子バッジ
    - **True**: 表示する
    - **False**: 表示しない
    """
    badge_grade: bool = field(default=False)
    """段位表示
    - **True**: 表示する
    - **False**: 表示しない
    """

    plotting_backend: Literal["matplotlib", "plotly"] = field(default="matplotlib")
    """グラフ描写ライブラリ"""

    def read_file(self, selected_service: str):
        """設定値取り込み

        Args:
            selected_service (str): セクション

        Raises:
            TypeError: 無効な型が指定されている場合
        """

        if self.config_file is None:
            raise TypeError("Configuration file not specified.")

        value: Union[int, float, bool, str, list]
        if self.config_file.has_section(selected_service):
            for f in fields(self):
                if f.name.startswith("_"):
                    continue
                if self.config_file.has_option(selected_service, f.name):
                    if f.type is int:
                        value = self.config_file.getint(selected_service, f.name)
                    elif f.type is float:
                        value = self.config_file.getfloat(selected_service, f.name)
                    elif f.type is bool:
                        value = self.config_file.getboolean(selected_service, f.name)
                    elif f.type is str:
                        value = self.config_file.get(selected_service, f.name)
                    elif f.type is list:
                        value = [x.strip() for x in self.config_file.get(selected_service, f.name).split(",")]
                    else:
                        raise TypeError(f"Unsupported type: {f.type}")
                    setattr(self, f.name, value)


class FunctionsInterface(ABC):
    """個別関数インターフェース"""

    @abstractmethod
    def post_processing(self, m: MessageParserProtocol):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

    @abstractmethod
    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """スレッド情報の取得

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """
        return {}


class APIInterface(ABC):
    """アダプタAPIインターフェース"""

    @abstractmethod
    def post(self, m: MessageParserProtocol):
        """メッセージを出力する

        Args:
            m (MessageParserProtocol): メッセージデータ
        """


class MessageParserDataMixin:
    """メッセージ解析共通処理"""

    data: "MsgData"
    post: "PostData"
    status: "StatusData"

    @property
    def in_thread(self) -> bool:
        """スレッド内のメッセージか判定"""
        if self.data.thread_ts == "0":
            return False
        if self.data.event_ts == self.data.thread_ts:
            return False
        return True

    @property
    def keyword(self) -> str:
        """コマンドとして認識している文字列を返す

        Returns:
            str: コマンド名
        """

        if (ret := self.data.text.split()):
            return ret[0]
        return self.data.text

    @property
    def argument(self) -> list:
        """コマンド引数として認識している文字列をリストで返す

        Returns:
            list: 引数リスト
        """

        if (ret := self.data.text.split()):
            return ret[1:]
        return ret

    @property
    def reply_ts(self) -> str:
        """リプライ先のタイムスタンプを取得する

        Returns:
            str: タイムスタンプ
        """

        ret_ts: str = "0"

        # tsが指定されていれば最優先
        if self.post.ts != "undetermined":
            return self.post.ts

        # スレッドに返すか
        if self.post.thread and self.in_thread:  # スレッド内
            if self.data.thread_ts != "undetermined":
                ret_ts = self.data.thread_ts
        elif self.post.thread and not self.in_thread:  # スレッド外
            ret_ts = self.data.event_ts

        return ret_ts

    def reset(self) -> None:
        """初期化"""

        self.data.reset()
        self.post.reset()
        self.status.reset()

    def get_score(self, keyword: str) -> dict:
        """textからスコアを抽出する

        Args:
            keyword (str): 成績報告キーワード

        Returns:
            dict: 結果
        """

        text = self.data.text
        ret: dict = {}

        # 記号を置換
        replace_chr = [
            (chr(0xff0b), "+"),  # 全角プラス符号
            (chr(0x2212), "-"),  # 全角マイナス符号
            (chr(0xff08), "("),  # 全角丸括弧
            (chr(0xff09), ")"),  # 全角丸括弧
            (chr(0x2017), "_"),  # DOUBLE LOW LINE(半角)
        ]
        for z, h in replace_chr:
            text = text.replace(z, h)

        text = "".join(text.split())  # 改行削除

        # パターンマッチング
        pattern1 = re.compile(
            rf"^({keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
        )
        pattern2 = re.compile(
            r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})$"
        )
        pattern3 = re.compile(
            rf"^({keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
        )
        pattern4 = re.compile(
            r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})\((.+?)\)$"
        )

        # 情報取り出し
        position: dict[str, int] = {}
        match text:
            case text if pattern1.findall(text):
                msg = pattern1.findall(text)[0]
                position = {
                    "p1_name": 1, "p1_str": 2,
                    "p2_name": 3, "p2_str": 4,
                    "p3_name": 5, "p3_str": 6,
                    "p4_name": 7, "p4_str": 8,
                }
                comment = None
            case text if pattern2.findall(text):
                msg = pattern2.findall(text)[0]
                position = {
                    "p1_name": 0, "p1_str": 1,
                    "p2_name": 2, "p2_str": 3,
                    "p3_name": 4, "p3_str": 5,
                    "p4_name": 6, "p4_str": 7,
                }
                comment = None
            case text if pattern3.findall(text):
                msg = pattern3.findall(text)[0]
                position = {
                    "p1_name": 2, "p1_str": 3,
                    "p2_name": 4, "p2_str": 5,
                    "p3_name": 6, "p3_str": 7,
                    "p4_name": 8, "p4_str": 9,
                }
                comment = str(msg[1])
            case text if pattern4.findall(text):
                msg = pattern4.findall(text)[0]
                position = {
                    "p1_name": 0, "p1_str": 1,
                    "p2_name": 2, "p2_str": 3,
                    "p3_name": 4, "p3_str": 5,
                    "p4_name": 6, "p4_str": 7,
                }
                comment = str(msg[9])
            case _:
                return ret

        for k, p in position.items():
            ret.update({k: str(msg[p])})

        ret.update(comment=comment)
        ret.update(ts=self.data.event_ts)

        return ret

    def get_remarks(self, keyword: str) -> list:
        """textからメモを抽出する

        Args:
            keyword (str): メモ記録キーワード

        Returns:
            list: 結果
        """

        ret: list = []
        if re.match(rf"^{keyword}", self.data.text):  # キーワードが先頭に存在するかチェック
            text = self.data.text.replace(keyword, "").strip().split()
            for name, matter in zip(text[0::2], text[1::2]):
                ret.append([name, matter])

        return ret


class MessageParserInterface(ABC):
    """メッセージ解析インターフェース"""

    @abstractmethod
    def parser(self, body: Any):
        """メッセージ解析

        Args:
            body (Any): 解析データ
        """

    @property
    @abstractmethod
    def is_command(self) -> bool:
        """コマンドで実行されているか

        Returns:
            bool: 真偽値
            - **True** : コマンド
            - **False** : 非コマンド(キーワード呼び出し)
        """

    @property
    @abstractmethod
    def is_bot(self) -> bool:
        """botのポストか

        Returns:
            bool: 真偽値
            - **True** : botのポスト
            - **False** : ユーザのポスト
        """

    @property
    @abstractmethod
    def check_updatable(self) -> bool:
        """DB操作の許可チェック

        Returns:
            bool: 真偽値
            - **True** : 許可
            - **False** : 禁止
        """

    @property
    @abstractmethod
    def ignore_user(self) -> bool:
        """ignore_useridに存在するユーザか

        Returns:
            bool: 真偽値
            - **True** : 存在する(操作禁止ユーザ)
            - **False** : 存在しない
        """
