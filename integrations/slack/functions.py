"""
integrations/slack/functions.py
"""

import logging
from typing import cast

from slack_sdk.errors import SlackApiError

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.base.interface import FunctionsInterface
from integrations.protocols import MessageParserProtocol
from integrations.slack.adapter import AdapterInterface


class SlackFunctions(FunctionsInterface):
    """slack専用関数"""

    def __init__(self, adapter: AdapterInterface):
        super().__init__()
        self.adapter = adapter

    def get_messages(self, word: str) -> list[MessageParserProtocol]:
        """slackログからメッセージを検索して返す

        Args:
            word (str): 検索するワード

        Returns:
            list[MessageParserProtocol]: 検索した結果
        """

        # 検索クエリ
        after = ExtDt(days=-self.adapter.conf.search_after).format("ymd", "-")
        query = f"{word} in:{self.adapter.conf.search_channel} after:{after}"
        logging.info("query=%s", query)

        # データ取得
        response = self.adapter.conf.webclient.search_messages(
            query=query,
            sort="timestamp",
            sort_dir="asc",
            count=100
        )
        matches = response["messages"]["matches"]  # 1ページ目
        for p in range(2, response["messages"]["paging"]["pages"] + 1):
            response = self.adapter.conf.webclient.search_messages(
                query=query,
                sort="timestamp",
                sort_dir="asc",
                count=100,
                page=p
            )
            matches += response["messages"]["matches"]  # 2ページ目以降

        # 必要なデータだけ辞書に格納
        data: list[MessageParserProtocol] = []
        for x in matches:
            if isinstance(x, dict):
                work_m = self.adapter.parser()
                work_m.parser(x)
                data.append(work_m)

        return data

    def get_message_details(self, matches: list[MessageParserProtocol]) -> list[MessageParserProtocol]:
        """メッセージ詳細情報取得

        Args:
            matches (list[MessageParserProtocol]): 対象データ

        Returns:
            list[MessageParserProtocol]: 詳細情報追加データ
        """

        new_matches: list[MessageParserProtocol] = []

        # 詳細情報取得
        for key in matches:
            conversations = self.adapter.conf.appclient.conversations_replies(channel=key.data.channel_id, ts=key.data.event_ts)
            if (msg := conversations.get("messages")):
                res = cast(dict, msg[0])
            else:
                continue

            if res:
                # 各種時間取得
                key.data.event_ts = str(res.get("ts", "0"))  # イベント発生時間
                key.data.thread_ts = str(res.get("thread_ts", "0"))  # スレッドの先頭
                key.data.edited_ts = str(cast(dict, res.get("edited", {})).get("ts", "0"))  # 編集時間
                # リアクション取得
                key.data.reaction_ok, key.data.reaction_ng = self.get_reactions_list(res)

            new_matches.append(key)

        return new_matches

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """スレッド情報の取得

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """

        try:
            res = self.adapter.conf.appclient.conversations_replies(channel=m.data.channel_id, ts=m.data.event_ts)
            logging.trace(res.validate())  # type: ignore
            return cast(dict, res)
        except SlackApiError as err:
            logging.error(err)
            return {}

    def get_reactions_list(self, msg: dict) -> tuple[list, list]:
        """botが付けたリアクションを取得

        Args:
            msg (dict): メッセージ内容

        Returns:
            tuple[list,list]:
            - reaction_ok: okが付いているメッセージのタイムスタンプ
            - reaction_ng: ngが付いているメッセージのタイムスタンプ
        """

        reaction_ok: list = []
        reaction_ng: list = []

        if msg.get("reactions"):
            for reactions in msg.get("reactions", {}):
                if isinstance(reactions, dict) and self.adapter.conf.bot_id in reactions.get("users", []):
                    match reactions.get("name"):
                        case self.adapter.conf.reaction_ok:
                            reaction_ok.append(msg.get("ts"))
                        case self.adapter.conf.reaction_ng:
                            reaction_ng.append(msg.get("ts"))

        return (reaction_ok, reaction_ng)

    def get_channel_id(self) -> str:
        """チャンネルIDを取得する

        Returns:
            str: チャンネルID
        """

        channel_id = ""

        try:
            response = self.adapter.conf.webclient.search_messages(
                query=f"in:{self.adapter.conf.search_channel}",
                count=1,
            )
            messages: dict = response.get("messages", {})
            if messages.get("matches"):
                channel = messages["matches"][0]["channel"]
                if isinstance(self.adapter.conf.search_channel, str):
                    if channel["name"] in self.adapter.conf.search_channel:
                        channel_id = channel["id"]
                else:
                    channel_id = channel["id"]
        except SlackApiError as err:
            logging.error(err)

        return channel_id

    def get_dm_channel_id(self, user_id: str) -> str:
        """DMのチャンネルIDを取得する

        Args:
            user_id (str): DMの相手

        Returns:
            str: チャンネルID
        """

        channel_id = ""

        try:
            response = self.adapter.conf.appclient.conversations_open(users=[user_id])
            channel_id = response["channel"]["id"]
        except SlackApiError as e:
            logging.error(e)

        return channel_id

    def pickup_score(self) -> list[MessageParserProtocol]:
        """過去ログからスコア記録を検索して返す

        Returns:
            list[MessageParserProtocol]: 検索した結果
        """

        score_matches: list[MessageParserProtocol] = []

        # ゲーム結果の抽出
        for match in self.get_messages(g.cfg.setting.keyword):
            if match.get_score(g.cfg.setting.keyword):
                if match.data.user_id in self.adapter.conf.ignore_userid:  # 除外ユーザからのポストは破棄
                    logging.info("skip ignore user: %s", match.data.user_id)
                    continue

                score_matches.append(match)

        # イベント詳細取得
        if score_matches:
            return self.get_message_details(score_matches)
        return score_matches

    def pickup_remarks(self) -> list[MessageParserProtocol]:
        """slackログからメモを検索して返す

        Returns:
            list[MessageParserProtocol]: 検索した結果
        """

        remarks_matches: list[MessageParserProtocol] = []

        # メモの抽出
        for match in self.get_messages(g.cfg.setting.remarks_word):
            if match.data.user_id in self.adapter.conf.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s", match.data.user_id)
                continue

            if (remark := match.get_remarks(g.cfg.setting.remarks_word)):
                match.data.remarks = remark
            else:  # 不一致は破棄
                continue

            remarks_matches.append(match)

        # イベント詳細取得
        if remarks_matches:
            return self.get_message_details(remarks_matches)
        return remarks_matches

    def post_processing(self, m: MessageParserProtocol):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        # リアクション処理
        match m.status.action:
            case "nothing":
                return
            case "change":
                for ts in m.status.target_ts:
                    reaction_data = self.adapter.api.reaction_status(ch=m.data.channel_id, ts=ts)
                    if m.status.reaction:  # NGを外してOKを付ける
                        if not reaction_data.get("ok"):
                            self.adapter.api.reaction_append(icon=self.adapter.conf.reaction_ok, ch=m.data.channel_id, ts=ts)
                        if reaction_data.get("ng"):
                            self.adapter.api.reaction_remove(icon=self.adapter.conf.reaction_ng, ch=m.data.channel_id, ts=ts)
                    else:  # OKを外してNGを付ける
                        if reaction_data.get("ok"):
                            self.adapter.api.reaction_remove(icon=self.adapter.conf.reaction_ok, ch=m.data.channel_id, ts=ts)
                        if not reaction_data.get("ng"):
                            self.adapter.api.reaction_append(icon=self.adapter.conf.reaction_ng, ch=m.data.channel_id, ts=ts)
                m.status.reset()
            case "delete":
                for ts in m.status.target_ts:
                    self.adapter.api.reaction_remove(icon=self.adapter.conf.reaction_ok, ch=m.data.channel_id, ts=ts)
                    self.adapter.api.reaction_remove(icon=self.adapter.conf.reaction_ng, ch=m.data.channel_id, ts=ts)
                m.status.reset()
