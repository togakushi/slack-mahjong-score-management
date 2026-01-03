"""cls/rule.py"""

import logging
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Mapping

from table2ascii import Alignment, PresetStyle, table2ascii

from cls.command import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class RuleData:
    """ルールデータ"""

    # ルール
    rule_version: str = ""
    """ルールバージョン識別子"""
    mode: Literal[3, 4] = 4
    """ 集計モード切替(四人打ち/三人打ち)"""
    origin_point: int = 250
    """配給原点"""
    return_point: int = 300
    """返し点"""
    rank_point: list[int] = field(default_factory=list)
    """順位点"""
    ignore_flying: bool = False
    """トビカウント
    - *True*: なし
    - *False*: あり
    """
    draw_split: bool = False
    """同点時の順位点
    - *True*: 山分けにする
    - *False*: 席順で決める
    """

    # ステータス
    first_time: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
    """記録開始日時"""
    last_time: ExtDt = field(default=ExtDt("1900-01-01 00:00:00"))
    """最終記録日時"""
    count: int = 0
    """記録回数"""

    def update(self, rule_data: Mapping[str, Any]):
        """ルール更新

        Args:
            rule_data (Mapping): 更新データ
        """

        if "rule_version" in rule_data:
            self.rule_version = str(rule_data["rule_version"])
        if "origin_point" in rule_data:
            self.origin_point = int(rule_data["origin_point"])
        if "return_point" in rule_data:
            self.return_point = int(rule_data["return_point"])

        if rank_point := rule_data.get("rank_point"):
            if isinstance(rank_point, str):
                rank_point = rank_point.split(",")
                self.rank_point = list(map(int, map(float, rank_point[: self.mode])))
            if isinstance(rank_point, list):
                self.rank_point = list(map(int, map(float, rank_point[: self.mode])))

        if ignore_flying := rule_data.get("ignore_flying"):
            if isinstance(ignore_flying, bool):
                self.ignore_flying = ignore_flying
            else:
                self.ignore_flying = str(ignore_flying).lower() in {"1", "true", "yes", "on"}
        else:
            self.ignore_flying = False

        if draw_split := rule_data.get("draw_split"):
            if isinstance(draw_split, bool):
                self.draw_split = draw_split
            else:
                self.draw_split = str(draw_split).lower() in {"1", "true", "yes", "on"}
        else:
            self.draw_split = False


class RuleSet:
    """ルールセット"""

    def __init__(self, config: "Path"):
        self.config: "Path" = config
        """ルール設定ファイルパス"""
        self.data: dict[str, RuleData] = {}
        """ルール情報格納辞書"""
        self.keyword_mapping: dict[str, str] = {}
        """登録キーワードとルールバージョン識別子のマッピング"""

        self.read_config()

    def data_set(
        self,
        version: str,
        mode: Literal[3, 4] = 4,
        rule_data: Mapping[str, Any] | None = None,
    ) -> bool:
        """ルール登録

        Args:
            version (str): ルールバージョン識別子
            mode (Literal[3, 4], optional): 四人打ち/三人打ち. Defaults to 四人打ち.
            rule_data (Mapping, optional): 更新データ情報

        Returns:
            bool: 登録結果真偽
        """

        rule = RuleData()
        rule.mode = mode
        rule.rule_version = version

        match rule.mode:
            case 3:
                rule.origin_point = 350
                rule.return_point = 400
                rule.rank_point = [30, 0, -30]
            case 4:
                rule.origin_point = 250
                rule.return_point = 300
                rule.rank_point = [30, 10, -10, -30]
            case _:
                logging.warning("Do not register: %s (invalid mode: %s)", version, mode)
                return False

        rule.ignore_flying = False
        rule.draw_split = False

        if rule_data:
            rule.update(rule_data)

        self.data.update({version: rule})
        return True

    def read_config(self):
        """設定ファイル読み込み"""

        rule_parser = ConfigParser()
        rule_parser.read(self.config)

        for section_name in rule_parser.sections():
            rule = dict(rule_parser[section_name])

            if self.data_set(section_name, mode=int(rule.get("mode", 4))):  # type: ignore
                self.data[section_name].update(rule)

    def status_update(self, version: str, **kwargs):
        """ステータス更新

        Args:
            version (str): ルールバージョン識別子
            kwargs (dict): 更新情報
        """

        if self.data.get(version):
            if "count" in kwargs and isinstance(kwargs["count"], int):
                self.data[version].count = kwargs["count"]
            if "first_time" in kwargs and isinstance(kwargs["first_time"], ExtDt):
                self.data[version].first_time = kwargs["first_time"]
            if "last_time" in kwargs and isinstance(kwargs["last_time"], ExtDt):
                self.data[version].last_time = kwargs["last_time"]

    def to_dict(self, version: str) -> dict[str, Any]:
        """指定ルールバージョン識別子の情報を辞書で返す

        Args:
            version (str): ルールバージョン識別子

        Returns:
            dict[str, Any]: ルール情報
        """

        if rule := self.data.get(version):
            return {
                "rule_version": rule.rule_version,
                "mode": rule.mode,
                "origin_point": rule.origin_point,
                "return_point": rule.return_point,
                "rank_point": rule.rank_point,
                "ignore_flying": rule.ignore_flying,
                "draw_split": rule.draw_split,
            }

        return {}

    def get_version(self, mode: int, mapping: bool = True) -> list[str]:
        """指定した条件のルールバージョン識別子をリストで返す

        Args:
            mode (int): 集計モード
            mapping (bool, optional): Defaults to True.
                - *True*: キーワードマッピングに登録されているルールのみ
                - *False*: ルールとして定義されているものすべて

        Returns:
            list[str]: ルールバージョン識別子
        """

        ret: list[str] = []

        for keyword, rule in self.data.items():
            if rule.mode == mode:
                if mapping:
                    if keyword in self.keyword_mapping.values():
                        ret.append(rule.rule_version)
                else:
                    ret.append(rule.rule_version)

        return ret

    def get_mode(self, version: str) -> int:
        """指定ルールバージョン識別子の集計モードを返す

        Args:
            version (str): ルールバージョン識別子

        Returns:
            int: 集計モード
        """

        return int(self.to_dict(version).get("mode", 0))

    def print(self, version: str) -> str:
        """指定ルールバージョン識別子の内容を出力する

        Args:
            version (str): ルールバージョン識別子

        Returns:
            str: 内容
        """

        ret: str = ""
        body_data: list = []

        if rule := self.data.get(version):
            body_data.append(["ルールバージョン", rule.rule_version])

            # 集計モード
            match rule.mode:
                case 3:
                    body_data.append(["集計モード", "三人打ち"])
                case 4:
                    body_data.append(["集計モード", "四人打ち"])
                case _:
                    body_data.append(["集計モード", "未定義"])

            body_data.extend(
                [
                    ["点数", f"{rule.origin_point * 100}点持ち / {rule.return_point * 100}点返し"],
                    ["順位点", " / ".join([f"{pt}pt".replace("-", "▲") for pt in rule.rank_point])],
                    ["同点時", "順位点山分け" if rule.draw_split else "席順"],
                ]
            )

            # マッピング情報
            if keyword := [word for word, rule_version in self.keyword_mapping.items() if rule_version == version]:
                body_data.append(["成績登録キーワード", "、".join(keyword)])
            else:
                body_data.append(["成績登録キーワード", "---"])

            # 記録時間
            body_data.append(["記録数", f"{rule.count} ゲーム"])
            if rule.count:
                body_data.extend(
                    [
                        ["記録開始日時", rule.first_time.format("ymdhms")],
                        ["最終記録日時", rule.last_time.format("ymdhms")],
                    ]
                )

            ret = table2ascii(
                body=body_data,
                alignments=[Alignment.LEFT, Alignment.LEFT],
                style=PresetStyle.plain,
            )

        return ret

    def info(self):
        """定義ルールをログに出力する"""

        logging.info("keyword_mapping: %s", self.keyword_mapping)
        for rule in self.data.values():
            logging.info(
                "%s: mode=%s, origin_point=%s, return_point=%s, rank_point=%s, draw_split=%s, ignore_flying=%s",
                rule.rule_version,
                rule.mode,
                rule.origin_point,
                rule.return_point,
                rule.rank_point,
                rule.draw_split,
                rule.ignore_flying,
            )

    def check(self, chk_commands: set, chk_members: set):
        """キーワード重複チェック

        Args:
            chk_commands (set): チェック対象コマンド名
            chk_members (set): チェック対象メンバー名/チーム名

        Raises:
            RuntimeError: 重複あり
        """

        chk_word: str | "RuleData"

        try:
            # ルール識別子チェック
            for chk_word in self.data.values():
                if CommandParser().is_valid_command(chk_word.rule_version):
                    raise RuntimeError(f"ルール識別子にオプションに使用される単語が使用されています。({chk_word.rule_version})")
                if chk_word.rule_version in ExtDt.valid_keywords():
                    raise RuntimeError(f"ルール識別子に検索範囲指定に使用される単語が使用されています。({chk_word.rule_version})")
                if chk_word.rule_version in chk_commands:
                    raise RuntimeError(f"ルール識別子と定義済みコマンドに重複があります。({chk_word.rule_version})")
                if chk_word.rule_version in chk_members:
                    raise RuntimeError(f"ルール識別子と登録メンバー(チーム)に重複があります。({chk_word.rule_version})")
            # 成績登録ワードチェック
            for chk_word in self.keyword_mapping.keys():
                if CommandParser().is_valid_command(chk_word):
                    raise RuntimeError(f"成績登録ワードにオプションに使用される単語が使用されています。({chk_word})")
                if chk_word in ExtDt.valid_keywords():
                    raise RuntimeError(f"成績登録ワードに検索範囲指定に使用される単語が使用されています。({chk_word})")
                if chk_word in chk_commands:
                    raise RuntimeError(f"成績登録ワードと定義済みコマンドに重複があります。({chk_word})")
                if chk_word in chk_members:
                    raise RuntimeError(f"成績登録ワードと登録メンバー(チーム)に重複があります。({chk_word})")
        except RuntimeError as err:
            logging.critical("%s", err)
            sys.exit(1)

    @property
    def rule_list(self) -> list[str]:
        """ルールセットの列挙

        Returns:
            list[str]: ルールセット
        """

        return list(self.data.keys())
