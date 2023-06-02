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


def post_text(client, channel, title, msg):
    if len(re.sub(r'\n+', '\n', f"{msg.strip()}").splitlines()) == 1:
        res = client.chat_postMessage(
            channel = channel,
            text = f"{title}\n{msg.strip()}",
        )
    else:
        res = client.chat_postMessage(
            channel = channel,
            text = f"\n{title}\n\n```{msg.strip()}```",
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
