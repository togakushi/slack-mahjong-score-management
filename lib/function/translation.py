import unicodedata


def len_count(text):
    """
    文字数をカウント(全角文字は2)

    Parameters
    ----------
    text : text
        判定文字列

    Returns
    -------
    count : int
        文字数
    """

    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return(count)


def HAN2ZEN(text):
    """
    半角文字を全角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(HAN, ZEN)
    return(text.translate(trans_table))


def ZEN2HAN(text):
    """
    全角文字を半角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(ZEN, HAN)
    return(text.translate(trans_table))


def HIRA2KANA(text):
    """
    ひらがなをカタカナに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(HIRA, KANA)
    return(text.translate(trans_table)) 


def KANA2HIRA(text):
    """
    カタカナをひらがなに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(KANA, HIRA)
    return(text.translate(trans_table)) 
