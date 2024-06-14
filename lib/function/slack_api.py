import re

from lib.function import global_value as g


def call_chat_postMessage(client, **kwargs):
    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = client.chat_postMessage(**kwargs)
    except g.SlackApiError as e:
        g.logging.error(e)

    return(res)


def call_files_upload(client, **kwargs):
    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = client.files_upload_v2(**kwargs)
    except g.SlackApiError as e:
        g.logging.error(e)

    return(res)


def post_message(client, channel, msg, ts = False):
    res = call_chat_postMessage(
        client,
        channel = channel,
        text = f"{msg.strip()}",
        thread_ts = ts,
    )

    return(res)


def post_multi_message(client, channel, msg, ts = False, summarize = True):
    if type(msg) == dict:
        if summarize: # まとめてポスト
            key_list = list(msg.keys())
            post_msg = msg[key_list[0]]
            for i in key_list[1:]:
                if len((post_msg + msg[i]).splitlines()) < 95: # 95行を超える直前までまとめる
                    post_msg += msg[i]
                else:
                    post_message(client, channel, post_msg, ts)
                    post_msg = msg[i]
            else:
                post_message(client, channel, post_msg, ts)
        else: # そのままポスト
            for i in msg.keys():
                post_message(client, channel, msg[i], ts)
    else:
        post_message(client, channel, msg, ts)


def post_text(client, channel, event_ts, title, msg):
    # コードブロック修飾付きポスト
    if len(re.sub(r"\n+", "\n", f"{msg.strip()}").splitlines()) == 1:
        res = call_chat_postMessage(
            client,
            channel = channel,
            text = f"{title}\n{msg.strip()}",
            thread_ts = event_ts,
        )
    else:
        # ポスト予定のメッセージをstep行単位のブロックに分割
        step = 50
        post_msg = []
        for count in range(int(len(msg.splitlines()) / step) + 1):
            post_msg.append("\n".join(msg.splitlines()[count * step:(count + 1) * step]))

        # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
        if len(post_msg) > 1 and step / 2 > len(post_msg[count].splitlines()):
            post_msg[count - 1] += "\n" + post_msg.pop(count)

        # ブロック単位でポスト
        for i in range(len(post_msg)):
            res = call_chat_postMessage(
                client,
                channel = channel,
                text = f"\n{title}\n\n```{post_msg[i].strip()}```",
                thread_ts = event_ts,
            )

    return(res)


def post_fileupload(client, channel, title, file, ts = False):
    res = call_files_upload(
        client,
        channel = channel,
        title = title,
        file = file,
        thread_ts = ts,
        request_file_info = False,
    )

    return(res)


def slack_post(**kwargs):
    g.logging.debug(f"{kwargs}")
    client = kwargs["client"] if "client" in kwargs else None
    channel = kwargs["channel"] if "channel" in kwargs else None
    headline = kwargs["headline"] if "headline" in kwargs else None
    message = kwargs["message"] if "message" in kwargs else None
    summarize = kwargs["summarize"] if "summarize" in kwargs else True
    file_list = kwargs["file_list"] if "file_list" in kwargs else {}

    # 見出しポスト
    res = post_message(client, channel, headline)

    # 本文ポスト
    if file_list:
        for x in file_list.keys():
            post_fileupload(client, channel, x, file_list[x], res["ts"])
    else:
        if message:
            post_multi_message(client, channel, message, res["ts"], summarize)
