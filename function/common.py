import re
import unicodedata
import datetime
from dateutil.relativedelta import relativedelta


def len_count(text): # 文字数
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return(count)


def HAN2ZEN(text): # 全角変換(数字のみ)
    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(HAN, ZEN)
    return(text.translate(trans_table))


def ZEN2HAN(text): # 半角変換(数字のみ)
    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(ZEN, HAN)
    return(text.translate(trans_table))


def HIRA2KANA(text):
    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(HIRA, KANA)
    return(text.translate(trans_table)) 


def KANA2HIRA(text):
    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(KANA, HIRA)
    return(text.translate(trans_table)) 


def scope_coverage(keyword = None):
    currenttime = datetime.datetime.now()
    if currenttime.hour < 12:
        startday = currenttime - datetime.timedelta(days = 1)
        endday = currenttime
    else:
        startday = currenttime
        endday = currenttime + datetime.timedelta(days = 1)

    if keyword:
        if re.match(r"^[0-9]{8}$", keyword):
            try:
                targettime = datetime.datetime(int(keyword[0:4]), int(keyword[4:6]), int(keyword[6:8]))
                startday = targettime
                endday = targettime + datetime.timedelta(days = 1)
            except:
                return(False, False)
        if keyword == "今月":
            startday = startday.replace(day = 1)
            endday = (endday + relativedelta(months = 1)).replace(day = 1)
        if keyword == "先月":
            startday = (startday - relativedelta(months = 1)).replace(day = 1)
            endday = endday.replace(day = 1)
        if keyword == "先々月":
            startday = (startday - relativedelta(months = 2)).replace(day = 1)
            endday = (endday - relativedelta(months = 1)).replace(day = 1)
        if keyword == "全部":
            startday = currenttime - datetime.timedelta(days = 91)
            endday = currenttime + datetime.timedelta(days = 1)

    return(
        startday.replace(hour = 12, minute = 0, second = 0, microsecond = 0), # starttime
        endday.replace(hour = 11, minute = 59, second = 59, microsecond = 999999), # endtime
    )
