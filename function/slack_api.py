

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

