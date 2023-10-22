import re

from lib.function import global_value as g

def Call_chat_postMessage(client, **kwargs):
    res = None
    try:
        if kwargs["thread_ts"]:
            res = client.chat_postMessage(
                channel = kwargs["channel"],
                text = kwargs["text"],
                thread_ts = kwargs["thread_ts"],
            )
        else:
            res = client.chat_postMessage(
                channel = kwargs["channel"],
                text = kwargs["text"],
            )
    except g.SlackApiError as e:
        g.logging.error(e)

    return(res)


def Call_files_upload(client, **kwargs):
    res = None
    try:
        if "file" in kwargs:
            res = client.files_upload(
                channels = kwargs["channels"],
                title = kwargs["title"],
                file = kwargs["file"],
            )
        if "content" in kwargs:
            res = client.files_upload(
                channels = kwargs["channels"],
                title = kwargs["title"],
                content = kwargs["content"],
            )
    except g.SlackApiError as e:
        g.logging.error(e)

    return(res)


def post_message(client, channel, msg, ts = False):
    res = Call_chat_postMessage(
        client,
        channel = channel,
        text = f"{msg.strip()}",
        thread_ts = ts,
    )

    return(res)


def post_text(client, channel, event_ts, title, msg):
    if len(re.sub(r"\n+", "\n", f"{msg.strip()}").splitlines()) == 1:
        res = Call_chat_postMessage(
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
            res = Call_chat_postMessage(
                client,
                channel = channel,
                text = f"\n{title}\n\n```{post_msg[i].strip()}```",
                thread_ts = event_ts,
            )

    return(res)


def post_upload(client, channel, title, msg):
    res = Call_files_upload(
        client,
        channels = channel,
        title = title,
        content = f"{msg.strip()}",
    )

    return(res)


def post_fileupload(client, channel, title, file):
    res = Call_files_upload(
        client,
        channels = channel,
        title = title,
        file = file,
    )

    return(res)
