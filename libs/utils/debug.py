"""
lib/utils/debug.py
"""


def debug_out(msg1: str, msg2: str | dict | list | bool | None = None) -> None:
    """メッセージ標準出力(テスト用)

    Args:
        msg1 (str): _description_
        msg2 (str | dict | list | bool | None, optional): _description_. Defaults to None.
    """

    print(msg1)
    if isinstance(msg2, dict):
        for _, val in msg2.items():
            print(val)
    elif msg2:
        print(msg2)
