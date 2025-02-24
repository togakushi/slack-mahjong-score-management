import re
from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

import lib.global_value as g
from lib.database.common import first_record


class SearchRange():
    """検索範囲取得クラス
    """

    words: dict = {}
    day_format = re.compile(r"^([0-9]{8}|[0-9/.-]{8,10})$")

    def __init__(self) -> None:
        self.first_record = first_record()
        self.update()

    def update(self) -> None:
        """キーワードから日付を取得する
        """

        self.current_time = datetime.now()
        self.appointed_time = self.current_time + relativedelta(hours=-12)
        self.words["当日"] = [
            self.appointed_time,
        ]
        self.words["今日"] = [
            self.current_time,
        ]
        self.words["昨日"] = [
            self.current_time + relativedelta(days=-1),
        ]
        self.words["今月"] = [
            self.appointed_time + relativedelta(day=1, months=0),
            self.appointed_time + relativedelta(day=1, months=1, days=-1),
        ]
        self.words["先月"] = [
            self.appointed_time + relativedelta(day=1, months=-1),
            self.appointed_time + relativedelta(day=1, months=0, days=-1),
        ]
        self.words["先々月"] = [
            self.appointed_time + relativedelta(day=1, months=-2),
            self.appointed_time + relativedelta(day=1, months=-1, days=-1),
        ]
        self.words["今年"] = [
            self.current_time + relativedelta(day=1, month=1),
            self.current_time + relativedelta(day=31, month=12),
        ]
        self.words["去年"] = [
            self.current_time + relativedelta(day=1, month=1, years=-1),
            self.current_time + relativedelta(day=31, month=12, years=-1),
        ]
        self.words["昨年"] = self.words["去年"]
        self.words["一昨年"] = [
            self.current_time + relativedelta(day=1, month=1, years=-2),
            self.current_time + relativedelta(day=31, month=12, years=-2),
        ]
        self.words["最初"] = [
            self.first_record + relativedelta(days=-1),
        ]
        self.words["最後"] = [
            self.current_time + relativedelta(days=1),
        ]
        self.words["全部"] = [
            self.first_record + relativedelta(days=-1),
            self.current_time + relativedelta(days=1),
        ]

    def find(self, word: str) -> bool:
        """指定ワード/日付が含まれているか判定する

        Args:
            word (str): チェックするワード or 日付

        Returns:
            bool: 真偽
        """

        if word in self.words:
            return (True)

        if re.match(self.day_format, word):
            return (True)
        return (False)

    def range(self, word: str):
        """指定ワードを日付に変換する

        Args:
            word (str): ワード

        Returns:
            list: 変換後の日付
        """

        self.update()
        if word in self.words:
            return (self.words[word])

        if re.match(self.day_format, word):
            try_day = pd.to_datetime(word, errors="coerce").to_pydatetime()
            if pd.isna(try_day):
                return ([])
            return ([try_day])

        return ([])

    def list(self):
        """ワードで指定できる範囲を一覧化する（ヘルプ表示用）

        Returns:
            str: ワードとその範囲
        """

        ret = []
        for key, val in self.words.items():
            days = []
            for v in val:
                days.append(v.strftime("%Y/%m/%d"))
            ret.append(f"{key}：{' ～ '.join(days)}")

        return ("\n".join(ret))


class CommandCheck(str):
    """キーワードがサブコマンドかチェックする(match専用)

    Args:
        str (str): チェックするキーワード

    Returns:
        bool: 真偽
    """

    def __init__(self, command_name: str):
        self.command_name = command_name

    def __eq__(self, chk_pattern: str) -> bool:
        commandlist = g.cfg.config["alias"].get(chk_pattern, "").split(",")
        commandlist = [chk_pattern] + [x for x in commandlist if x]

        if self.command_name in commandlist:
            return (True)

        return (False)
