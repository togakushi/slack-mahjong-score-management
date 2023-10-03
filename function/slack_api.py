import re


def post_message(client, channel, msg, ts = False):
    if ts:
        res = client.chat_postMessage(
            channel = channel,
            text = f"{msg.strip()}",
            thread_ts = ts,
        )
    else:
        res = client.chat_postMessage(
            channel = channel,
            text = f"{msg.strip()}",
        )

    return(res)


def post_text(client, channel, event_ts, title, msg):
    if len(re.sub(r'\n+', '\n', f"{msg.strip()}").splitlines()) == 1:
        res = client.chat_postMessage(
            channel = channel,
            text = f"{title}\n{msg.strip()}",
            thread_ts = event_ts,
        )
    else:
        # ポスト予定のメッセージをstep行単位のブロックに分割
        step = 50
        post_msg = []
        for count in range(int(len(msg.splitlines()) / step) + 1):
            post_msg.append('\n'.join(msg.splitlines()[count * step:(count + 1) * step]))

        # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
        if len(post_msg) > 1 and step / 2 > len(post_msg[count].splitlines()):
            post_msg[count - 1] += "\n" + post_msg.pop(count)

        # ブロック単位でポスト
        for i in range(len(post_msg)):
            res = client.chat_postMessage(
                channel = channel,
                text = f"\n{title}\n\n```{post_msg[i].strip()}```",
                thread_ts = event_ts,
            )

    return(res)


def post_upload(client, channel, title, msg):
    res = client.files_upload(
        channels = channel,
        title = title,
        content = f"{msg.strip()}",
    )

    return(res)


def post_fileupload(client, channel, title, file):
    res = client.files_upload(
        channels = channel,
        title = title,
        file = file,
    )

    return(res)
