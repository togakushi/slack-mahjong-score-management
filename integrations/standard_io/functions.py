"""
integrations/standard_io/functions.py
"""

from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.protocols import MessageParserProtocol
from libs.functions import message


def score_verification(detection: GameResult, m: MessageParserProtocol):
    """素点合計のチェック

    Args:
        detection (GameResult): ゲーム結果
        m (MessageParserProtocol): メッセージデータ
    """

    print(ExtDt(float(detection.ts)), detection.to_text("detail"))

    # 素点合計チェック
    if detection.deposit:
        m.post.rpoint_sum = detection.rpoint_sum()
        print(">", message.random_reply(m, "invalid_score", False))

    # プレイヤー名重複チェック
    if len(set(detection.to_list())) != 4:
        print(">", message.random_reply(m, "same_player", False))
