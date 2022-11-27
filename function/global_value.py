import logging
import os

from slack_sdk import WebClient
from slack_bolt import App

from function import option

args = option.parser()

app = App(token = os.environ["SLACK_BOT_TOKEN"])
webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])

if args.debug:
    print("DEBUG MODE")
    logging_level = logging.INFO
else:
    logging_level = logging.WARNING
