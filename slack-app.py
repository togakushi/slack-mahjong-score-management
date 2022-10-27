#!/usr/bin/env python3

import logging
import sys
import os
import re
import unicodedata
import random
import configparser

import datetime
from dateutil.relativedelta import relativedelta

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level = logging.ERROR)
app = App(token = os.environ["SLACK_BOT_TOKEN"])

# イベントAPI
@app.message(re.compile(r"^御無礼成績$"))
def handle_goburei1_evnts(client, context):
    title, msg = goburei_results()
    post_text(client, context.channel_id, title, msg)

@app.message(re.compile(r"^御無礼(記録|結果)$"))
def handle_goburei2_evnts(client, context):
    title, msg = goburei_record()
    post_upload(client, context.channel_id, title, msg)

@app.message(re.compile(r"^御無礼グラフ"))
def handle_goburei3_evnts(client, context, body):
    v = body["event"]["text"].split()
    starttime = False
    endtime = False
    if len(v) == 1:
        starttime, endtime = scope_coverage()
    elif len(v) == 2:
        if re.match(r"^(今月|先月|先々月)$", v[1]):
            starttime, endtime = scope_coverage(v[1])
        if re.match(r"^[0-9]{8}$", v[1]):
            starttime, endtime = scope_coverage(v[1])

    if starttime or endtime:
        count = goburei_graph(starttime, endtime)
        file = os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png")
        if count <= 0:
            msg = f"{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')} に御無礼はありません。"
            post_message(client, context.channel_id, msg)
        else:
            post_fileupload(client, context.channel_id, "御無礼グラフ", file)
    else:
        msg = f"？"
        post_message(client, context.channel_id, msg)

@app.message(re.compile(r"御無礼"))
def handle_goburei_check_evnts(client, body):
    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    msg = goburei_pattern(body["event"]["text"])
    if msg:
        s = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])
        if not s == 1000:
            msg = random.choice([
                f"<@{user_id}> {abs(1000-s)*100}点合わないようです。",
                f"<@{user_id}> {abs(1000-s)*100}点合いませんが。",
                f"<@{user_id}> {abs(1000-s)*100}点合いません。ご確認を。",
                f"<@{user_id}> ・・・。{abs(1000-s)*100}点合ってませんね・・・。",
            ])
            post_message(client, channel_id, msg)

@app.command("/goburei")
def goburei_command(ack, body, client):
    ack()
    global player_list
    user_id = body["user_id"]
    msg = ""

    if body["text"]:
        subcom = body["text"].split()[0]

        if subcom.lower() in ("member", "userlist", "メンバー", "リスト"):
            title = "登録されているメンバー"
            for player in player_list.sections():
                if player == "DEFAULT":
                    continue
                alias = player_list.get(player, "alias")
                msg += f"{player} -> {alias.split(',')}\n"
            post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("results", "成績"):
            title, msg = goburei_results()
            post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("allresults", "全成績"):
            title, msg = goburei_results(name_replace = False, guest_skip = False)
            title = datetime.datetime.now().strftime("今月の成績(名前ブレ修正なし、敬称略) [%Y/%m/%d %H:%M 集計]")
            post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("record", "記録", "結果"):
            title, msg = goburei_record()
            post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("allrecord", "全記録", "全結果"):
            title, msg = goburei_record(name_replace = False, guest_skip = False)
            title = datetime.datetime.now().strftime("集計済みデータ(名前ブレ修正なし、敬称略)")
            post_upload(client, user_id, title, msg)
            return

        if subcom.lower() in ("details", "詳細", "個人", "個人成績"):
            opt = body["text"].split()
            if not len(opt) == 1:
                pname = NameReplace(opt[1], guest = False)
                if pname in player_list.sections():
                    data = goburei_search(name_replace = True, guest_skip = False, tmonth = True)
                    msg1 = datetime.datetime.now().strftime(f"*【%Y年%m月の個人成績(※2ゲスト戦含む)】*\n")
                    msg2 = datetime.datetime.now().strftime(f"\n*【%Y年%m月の戦績】*\n")

                    point = 0
                    count_rank = [0, 0, 0, 0]
                    count_tobi = 0
                    count_win = 0
                    count_lose = 0
                    count_draw = 0

                    for i in range(len(data)):
                        for seki in ("東家", "南家", "西家", "北家"):
                            if pname == data[i][seki]["name"]:
                                count_rank[data[i][seki]["rank"] -1] += 1
                                point += float(data[i][seki]["point"])
                                count_tobi += 1 if eval(data[i][seki]["rpoint"]) < 0 else 0
                                count_win += 1 if float(data[i][seki]["point"]) > 0 else 0
                                count_lose += 1 if float(data[i][seki]["point"]) < 0 else 0
                                count_draw += 1 if float(data[i][seki]["point"]) == 0 else 0
                                msg2 += "{}： {}位 {:>5}00点 ({:>+5.1f}) {}\n".format(
                                    data[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"),
                                    data[i][seki]["rank"], eval(data[i][seki]["rpoint"]), float(data[i][seki]["point"]),
                                    "※" if [data[i][x]["name"] for x in ("東家", "南家", "西家", "北家")].count("ゲスト１") >= 2 else "",
                                ).replace("-", "▲")
                    msg1 += "プレイヤー名： {}\n対戦数： {} 半荘 ({} 勝 {} 敗 {} 分)\n".format(
                        pname, sum(count_rank), count_win, count_lose, count_draw,
                    )
                    if sum(count_rank) > 0:
                        msg1 += "累積ポイント： {:+.1f}\n平均ポイント： {:+.1f}\n".format(
                            point, point / sum(count_rank),
                        ).replace("-", "▲")
                        for i in range(4):
                            msg1 += "{}位： {:2} 回 ({:.2%})\n".format(i + 1, count_rank[i], count_rank[i] / sum(count_rank))
                        msg1 += "トビ： {} 回 ({:.2%})\n".format(count_tobi, count_tobi / sum(count_rank))
                        msg1 += "平均順位： {:1.2f}\n".format(
                            sum([count_rank[i] * (i + 1) for i in range(4)]) / sum(count_rank),
                        )
                    else:
                        msg2 += f"記録なし\n"
                    msg2 += datetime.datetime.now().strftime(f"\n_(%Y/%m/%d %H:%M:%S 集計)_")
                else:
                    msg1 = f"「{pname}」は登録されていません。"
                    msg2 = ""
            else:
                msg1 = "使い方： /goburei details <登録名>"
                msg2 = ""
            post_message(client, user_id, msg1 + msg2)
            return

        if subcom.lower() in ("graph", "グラフ"):
            v = body["text"].split()
            if len(v) == 1:
                starttime, endtime = scope_coverage()
            elif len(v) == 2:
                if re.match(r"^(今月|先月|先々月)$", v[1]):
                    starttime, endtime = scope_coverage(v[1])
                if re.match(r"^[0-9]{8}$", v[1]):
                    starttime, endtime = scope_coverage(v[1])
                if not (starttime or endtime):
                    return
            else:
                return

            if starttime or endtime:
                count = goburei_graph(starttime, endtime)
                file = os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png")
                if count <= 0:
                    msg = f"{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')} に御無礼はありません。"
                    post_message(client, user_id, msg)
                else:
                    post_fileupload(client, user_id, "御無礼グラフ", file)
            else:
                msg = f"？"
                post_message(client, user_id, msg)

            return

        if subcom.lower() in ("load"):
            player_list = configload(sys.argv[1])
            post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in ("save"):
            configsave(player_list, sys.argv[1])
            post_message(client, user_id, f"メンバーリストを保存しました。")
            return

        if subcom.lower() in ("add", "追加"):
            v = body["text"].split()
            msg = "使い方が間違っています。"
            if len(v) == 2: # 新規追加
                new_name = HAN2ZEN(v[1])
                if player_list.has_section(new_name):
                    msg = f"「{new_name}」はすでに登録されています。"
                else:
                    if len(player_list.keys()) > 255: # 登録上限チェック
                        msg = f"登録上限を超えています。"
                    elif not check_namepattern(new_name):
                        msg = f"命名規則に違反しているので登録できません。"
                    else:
                        player_list.add_section(new_name)
                        player_list.set(new_name, "alias", new_name)
                        msg = f"「{new_name}」を登録しました。"
                post_message(client, user_id, msg)
                return

            if len(v) == 3: # 別名登録
                new_name = HAN2ZEN(v[1])
                nic_name = HAN2ZEN(v[2])
                # ダブりチェック
                checklist = []
                for player in player_list.sections():
                    checklist.append(player)
                    checklist += player_list.get(player, "alias").split(",")
                if nic_name in checklist:
                    msg = f"「{nic_name}」はすでに登録されています。"
                elif not check_namepattern(nic_name):
                    msg = f"命名規則に違反しているので登録できません。"
                else:
                    if player_list.has_section(new_name):
                        alias = player_list.get(new_name, "alias")
                        if len(alias.split(",")) > 16:
                            msg = f"登録上限を超えています。"
                        else:
                            player_list.set(new_name, "alias", ",".join([alias, nic_name]))
                            msg = f"「{new_name}」に「{nic_name}」を追加しました。"
                    else:
                        msg = f"「{new_name}」は登録されていません。"
                post_message(client, user_id, msg)
                return

        if subcom.lower() in ("del", "削除"):
            v = body["text"].split()
            msg = "使い方が間違っています。"
            if len(v) == 2: # メンバー削除
                if player_list.has_section(v[1]):
                    player_list.remove_section(v[1])
                    msg = f"「{v[1]}」を削除しました。"
            if len(v) == 3: # 別名削除
                if player_list.has_section(v[1]):
                    alias = player_list.get(v[1], "alias").split(",")
                    if v[1] == v[2]:
                        player_list.remove_section(v[1])
                        msg = f"「{v[1]}」を削除しました。"
                    if v[2] in alias:
                        alias.remove(v[2])
                        if len(alias) == 0:
                            player_list.remove_section(v[1])
                            msg = f"「{v[1]}」を削除しました。"
                        else:
                            player_list.set(v[1], "alias", ",".join(alias))
                            msg = f"「{v[1]}」から「{v[2]}」を削除しました。"
                    else:
                        msg = f"「{v[1]}」に「{v[2]}」は登録されていません。"

            post_message(client, user_id, msg)
            return

    msg = "使い方：\n"
    msg += "`{} {}` {}\n".format(body["command"], "help", "このメッセージ")
    msg += "`{} {}` {}\n".format(body["command"], "results", "今月の成績")
    msg += "`{} {}` {}\n".format(body["command"], "record", "張り付け用集計済みデータ出力")
    msg += "`{} {}` {}\n".format(body["command"], "allrecord", "集計済み全データ出力(名前ブレ修正なし)")
    msg += "`{} {}` {}\n".format(body["command"], "graph", "ポイント推移グラフを表示")
    msg += "`{} {} <名前>` {}\n".format(body["command"], "details", "2ゲスト戦含む個人成績出力")
    msg += "`{} {}` {}\n".format(body["command"], "member | userlist", "登録されているメンバー")
    msg += "`{} {}` {}\n".format(body["command"], "add", "メンバーの追加")
    msg += "`{} {}` {}\n".format(body["command"], "del", "メンバーの削除")
    msg += "`{} {}` {}\n".format(body["command"], "load", "メンバーリストの再読み込み")
    msg += "`{} {}` {}\n".format(body["command"], "save", "メンバーリストの保存")

    post_message(client, user_id, msg)

@app.event("message")
def handle_message_events():
    pass

# function
def post_message(client, channel, msg):
    client.chat_postMessage(
        channel = channel,
        text = f"{msg.strip()}",
    )

def post_text(client, channel, title, msg):
    client.chat_postMessage(
        channel = channel,
        text = f"\n{title}\n\n```{msg.strip()}```",
    )

def post_upload(client, channel, title, msg):
    client.files_upload(
        channels = channel,
        title = title,
        content = f"{msg.strip()}",
    )

def post_fileupload(client, channel, title, file):
    client.files_upload(
        channels = channel,
        title = title,
        file = file,
    )

def CalculationPoint(rpoint, rank): # 順位点計算
    oka = 20
    uma = [oka + 20, 10, -10, -20]
    point = (rpoint - 300) / 10 + uma[rank - 1]

    return(float(f"{point:>.1f}"))

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

def check_namepattern(name): # 登録制限チェック
    if len(name) > 8:
        return(False)
    if re.search("[\\\;:<>,!@#*?/`\"']", name):
        return(False)
    if not name.isprintable():
        return(False)
    return(True)

def NameReplace(pname, name_replace = True, guest = True): # 表記ブレ修正
    pname = pname.replace("さん", "")
    pname = HAN2ZEN(pname)

    if not name_replace:
        return(pname)

    for player in player_list.sections():
        for alias in player_list.get(player, "alias").split(","):
            if pname == alias:
                return(player)

    return("ゲスト１" if guest else pname)

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
            startday = currenttime.replace(day = 1)
            endday = (currenttime + relativedelta(months = 1)).replace(day = 1)
        if keyword == "先月":
            startday = (currenttime - relativedelta(months = 1)).replace(day = 1)
            endday = currenttime.replace(day = 1)
        if keyword == "先々月":
            startday = (currenttime - relativedelta(months = 2)).replace(day = 1)
            endday = (currenttime - relativedelta(months = 1)).replace(day = 1)

    return(
        startday.replace(hour = 12, minute = 0, second = 0, microsecond = 0), # starttime
        endday.replace(hour = 11, minute = 59, second = 59, microsecond = 999999), # endtime
    )

def configload(configfile):
    config = configparser.ConfigParser()

    try:
        config.read(configfile, encoding="utf-8")
    except:
        sys.exit()

    return(config)

def configsave(config, configfile):
    with open(configfile, "w") as f:
        config.write(f)

def goburei_results(name_replace = True, guest_skip = True, tmonth = True): # 御無礼成績
    title = datetime.datetime.now().strftime("今月の成績 [%Y/%m/%d %H:%M:%S 集計]")
    data = goburei_search(name_replace = name_replace, guest_skip = guest_skip, tmonth = tmonth)

    r = {}
    for i in range(len(data)):
        for seki in ("東家", "南家", "西家", "北家"):
            name = data[i][seki]["name"]
            if not name in r:
                r[name] = {
                    "total": 0,
                    "rank": [0, 0, 0, 0],
                }
            r[name]["total"] += round(data[i][seki]["point"], 2)
            r[name]["rank"][data[i][seki]["rank"] -1] += 1

    tmp_r = {}
    msg = ""
    for i in r.keys():
        tmp_r[i] = r[i]["total"]
    for u,p in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        msg += "{}{}： {:>+6.1f} ({:>+5.1f})".format(
            u, " " * (9 - len_count(u)),
            r[u]["total"],
            r[u]["total"] / sum(r[u]["rank"]),
        ).replace("-", "▲")
        msg += " / {}-{}-{}-{} ({:1.2f})\n".format(
            r[u]["rank"][0], r[u]["rank"][1], r[u]["rank"][2], r[u]["rank"][3],
            sum([r[u]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[u]["rank"]),
        )

    if not msg:
        msg = "御無礼なし"

    return(title, msg)

def goburei_record(name_replace = True, guest_skip = True, tmonth = False): # 御無礼結果
    title = datetime.datetime.now().strftime("張り付け用集計済みデータ")
    data = goburei_search(name_replace = name_replace, guest_skip = guest_skip, tmonth = tmonth)

    msg = ""
    for i in range(len(data)):
        deposit = 1000 - eval(data[i]["東家"]["rpoint"]) - eval(data[i]["南家"]["rpoint"]) - eval(data[i]["西家"]["rpoint"]) - eval(data[i]["北家"]["rpoint"])
        msg += "{},<場所>,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
            data[i]["日付"].strftime("%Y/%m/%d %H:%M"), deposit,
            data[i]["東家"]["name"], eval(data[i]["東家"]["rpoint"]), data[i]["東家"]["rank"], data[i]["東家"]["point"],
            data[i]["南家"]["name"], eval(data[i]["南家"]["rpoint"]), data[i]["南家"]["rank"], data[i]["南家"]["point"],
            data[i]["西家"]["name"], eval(data[i]["西家"]["rpoint"]), data[i]["西家"]["rank"], data[i]["西家"]["point"],
            data[i]["北家"]["name"], eval(data[i]["北家"]["rpoint"]), data[i]["北家"]["rank"], data[i]["北家"]["point"],
        )

    return(title, msg)

def goburei_graph(starttime, endtime): # 御無礼グラフ
    data = goburei_search(name_replace = True, guest_skip = True, tmonth = False)
    gdata = {}
    geme_time = []
    player_list = []
    for i in range(len(data)):
        if starttime < data[i]["日付"] and endtime > data[i]["日付"]:
            gdata[data[i]["日付"]] = []
            geme_time.append(data[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"))
            for seki in ("東家", "南家", "西家", "北家"):
                gdata[data[i]["日付"]].append((data[i][seki]["name"], data[i][seki]["point"]))
                if not data[i][seki]["name"] in player_list:
                    player_list.append(data[i][seki]["name"])

    stacked_point = {}
    for name in player_list:
        stacked_point[name] = []
        total_point = 0
        for i in gdata:
            point = 0
            for n, p in gdata[i]:
                if name == n:
                    point = p
            total_point = round(total_point + point, 2)
            stacked_point[name].append(total_point)
    # sort
    rank = {}
    for name in player_list:
        rank[name] = stacked_point[name][-1]
    ranking = sorted(rank.items(), key=lambda x:x[1], reverse=True)

    ### グラフ生成 ###
    fp = FontProperties(
        fname = os.path.join(os.path.realpath(os.path.curdir), "ipaexg.ttf"),
        size = 9,
    )
    fig = plt.figure()
    plt.xticks(rotation = 45)
    plt.style.use("ggplot")
    # サイズ、表記調整
    if len(geme_time) > 20:
        fig = plt.figure(figsize = (12 + 6 * int(len(geme_time) / 30), 6))
    if len(geme_time) > 6:
        plt.xticks(rotation = 90)
    if len(geme_time) == 1:
        plt.xticks(rotation = 0)

    plt.title(
        f"ポイント推移 ({starttime.strftime('%Y/%m/%d %H:%M')} - {endtime.strftime('%Y/%m/%d %H:%M')})",
        fontproperties = fp,
        fontsize = 12,
    )
    plt.hlines(y = 0, xmin = -100, xmax = 100, linewidth = 0.5, linestyles="dashed", color = "grey")
    plt.ylabel("累計ポイント", fontproperties = fp)

    for name, total in ranking:
        label = f"{name} ({str(total)})".replace("-", "▲")
        plt.plot(geme_time, stacked_point[name], marker = "o", markersize = 3, label = label)
    plt.legend(bbox_to_anchor = (1.05, 1), loc = "upper left", borderaxespad = 0, prop = fp)
    plt.tight_layout()
    fig.savefig(os.path.join(os.path.realpath(os.path.curdir), "goburei_graph.png"))
    return(len(gdata))

def goburei_search(name_replace = True, guest_skip = True, tmonth = False):
    currenttime = datetime.datetime.now()
    if currenttime.day == 1 and currenttime.hour < 12:
        currenttime = currenttime - datetime.timedelta(days = 1)
    am = datetime.datetime.fromisoformat(currenttime.strftime(f"%Y-%m-01 12:00:00.000000"))
    am = datetime.datetime.timestamp(am)

    ### データ取得 ###
    response = webclient.search_messages(
        query = "御無礼 in:#麻雀やろうぜ",
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = webclient.search_messages(
            query = "御無礼 in:#麻雀やろうぜ",
            sort = "timestamp",
            sort_dir = "asc",
            count = 100,
            page = p
        )
        matches += response["messages"]["matches"] # 2ページ目以降

    seat = {
        "東家": 0.000004, "南家": 0.000003, "西家": 0.000002, "北家": 0.000001,
    }

    data = {}
    count = 0
    for i in range(len(matches)):
        if "blocks" in matches[i]:
            ts = float(matches[i]["ts"])
            dt = datetime.datetime.fromtimestamp(ts)

            if tmonth and ts < am: # 一日の午前は先月からの続き
                continue

            if "elements" in matches[i]["blocks"][0]:
                msg = ""
                tmp = matches[i]["blocks"][0]["elements"][0]["elements"]
                for x in range(len(tmp)):
                    if tmp[x]["type"] == "text":
                        msg += tmp[x]["text"]
                msg = goburei_pattern(msg)

                if msg:
                    ### 表記ブレ修正 ###
                    for x in range(0, len(msg), 2):
                        msg[x] = NameReplace(msg[x], name_replace)

                    if guest_skip and msg.count("ゲスト１") >= 2:
                        continue

                    data[count] = {
                        "日付": dt,
                        "東家": {"name": msg[0], "rpoint": msg[1], "rank": None, "point": 0},
                        "南家": {"name": msg[2], "rpoint": msg[3], "rank": None, "point": 0},
                        "西家": {"name": msg[4], "rpoint": msg[5], "rank": None, "point": 0},
                        "北家": {"name": msg[6], "rpoint": msg[7], "rank": None, "point": 0},
                    }

                    ### 順位取得 ###
                    rank = [
                        eval(msg[1]) + seat["東家"],
                        eval(msg[3]) + seat["南家"],
                        eval(msg[5]) + seat["西家"],
                        eval(msg[7]) + seat["北家"],
                    ]
                    rank.sort()
                    rank.reverse()

                    for x, y in [("東家", 1), ("南家", 3), ("西家", 5), ("北家", 7)]:
                        p = eval(msg[y]) + seat[x]
                        data[count][x]["rank"] = rank.index(p) + 1
                        data[count][x]["point"] = CalculationPoint(eval(msg[y]), rank.index(p) + 1)

                    count += 1

    return(data)

def goburei_pattern(msg):
    pattern1 = re.compile(r"^御無礼 ?([^0-9+-]+ ?[0-9+-]+ ?){4}")
    pattern2 = re.compile(r"( ?[^0-9+-]+ ?[0-9+-]+){4} ?御無礼$")
    msg = "".join(msg.split())
    if pattern1.search(msg) or pattern2.search(msg):
        ret = msg.replace("御無礼", "")
        ret = re.sub(r"([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)", r"\1 \2 \3 \4 \5 \6 \7 \8", ret)
        ret = ret.split()
    return(ret if "ret" in locals() else False)

if __name__ == "__main__":
    player_list = configload(sys.argv[1])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
