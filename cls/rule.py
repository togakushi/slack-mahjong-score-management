"""cls/rule.py"""

import logging
from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Mapping

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class RuleData:
    """ルールデータ"""

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
        """デフォルト値のセット

        Args:
            version (str): ルールバージョン識別子
            mode (Literal[3, 4], optional): 四人打ち/三人打ち. Defaults to 四人打ち.
            rule_data (Mapping): data

        Returns:
            bool: 登録結果
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
        rule_parser = ConfigParser()
        rule_parser.read(self.config)

        for section_name in rule_parser.sections():
            rule = dict(rule_parser[section_name])

            if self.data_set(section_name, mode=int(rule.get("mode", 4))):  # type: ignore
                self.data[section_name].update(rule)

    def to_dict(self, version: str) -> dict:
        """指定ルールバージョン識別子の情報を辞書で返す

        Args:
            version (str): ルールバージョン識別子

        Returns:
            dict: ルールデータ
        """

        if rule := self.data.get(version):
            return rule.__dict__

        return {}

    def info(self):
        """ルールデータをログに出力する"""

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
