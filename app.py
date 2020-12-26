import os
import sys
from flask import Flask, jsonify, request, abort, send_file
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

line_bot_api = LineBotApi('/17kaODuHVm5GJBw6poJ8e61lpFclxKrDtShYevjBaDY2TuRjXMEU6+J6hTanMP6WL2LuQSWs2o9PbmAPN04P4sC9TiHNzJlgTiu2FUsL7qT85rIoapOQ/uDad4diIazLB20q4UdYmbBy77T4DwiawdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c969e2f78ea50f727549fa87f4989c31')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
