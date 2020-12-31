import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message, send_carousel_message, send_button_message, send_image_message

load_dotenv()


machine = TocMachine(
    states=["user", "menu", "weather", "planTour", "choosePosition", "show_fsm_pic",
            "enterPosition", "preference", "chooseRoute", "chat"],
    transitions=[
        {
            "trigger": "advance",
            "source": "user",
            "dest": "menu",
            "conditions": "is_going_to_menu",
        },
        {
            "trigger": "advance",
            "source": "menu",
            "dest": "weather",
            "conditions": "is_going_to_weather",
        },
        {
            "trigger": "advance",
            "source": "menu",
            "dest": "chat",
            "conditions": "is_going_to_chat",
        },
        {
            "trigger": "advance",
            "source": "menu",
            "dest": "planTour",
            "conditions": "is_going_to_planTour",
        },
        {
            "trigger": "advance",
            "source": "planTour",
            "dest": "preference",
            "conditions": "is_going_to_preference",
        },
        {
            "trigger": "advance",
            "source": "preference",
            "dest": "chooseRoute",
            "conditions": "is_going_to_chooseRoute",
        },
        {
             "trigger": "advance",
             "source": "menu",
             "dest": "show_fsm_pic",
             "conditions": "is_going_to_show_fsm_pic",
         },
        # {
        #     "trigger": "advance",
        #     "source": "planTour",
        #     "dest": "choosePosition",
        #     "conditions": "is_going_to_choosePosition",
        # },
        # {
        #     "trigger": "advance",
        #     "source": "choosePosition",
        #     "dest": "positioning",
        #     "conditions": "is_going_to_positioning",
        # },
        # {
        #     "trigger": "advance",
        #     "source": "planTour",
        #     "dest": "enterPosition",
        #     "conditions": "is_going_to_enterPosition",
        # },
        # {
        #     "trigger": "advance",
        #     "source": "enterPosition",
        #     "dest": "inputPosition",
        #     "conditions": "is_going_to_inputPosition",
        # },
        # {
        #     "trigger": "advance",
        #     "source": ["positioning", "inputPosition"],
        #     "dest": "preference",
        #     "conditions": "is_going_to_preference",
        # },
        {
            "trigger": "go_back", 
            "source": ["menu"], 
            "dest": "user"
        },
        {
            "trigger": "go_back_menu",
            "source": ["weather", "planTour","choosePosition","show_fsm_pic","positioning", "enterPosition", "inputPosition"],
            "dest": "menu",
        },
        {
            "trigger": "go_back_planTour",
            "source": ["preference", "choosePosition"],
            "dest": "planTour", 
        },
        {
            "trigger": "go_back_preference",
            "source": ["chooseRoute"],
            "dest": "preference",
        }
    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

mode = 0
@app.route('/callback', methods=['POST'])
def webhook_handler():
    global mode
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f'Request body: {body}')

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f'\nFSM STATE: {machine.state}')
        print(f'REQUEST BODY: \n{body}')

        if mode == 1:
            if event.message.text.lower() == 'menu':
                mode = 0
                send_text_message(event.reply_token, '返回主選單')
                continue
            else:
                send_text_message_AI(event.reply_token, event.message.text)
                continue
        else:
            if event.message.text.lower() == 'chat':
                mode = 1
                send_text_message(event.reply_token, '進入聊天模式，隨時輸入「menu」可返回主選單')
                continue
            else:
                response = machine.advance(event)

        if response == False:
            if event.message.text.lower() == 'fsm':
                send_image_message(event.reply_token, 'https://master-of-tour.herokuapp.com/show-fsm')
            elif machine.state != 'user' and event.message.text.lower() == 'restart':
                send_text_message(event.reply_token, '輸入「menu」即可進入主選單。\n隨時輸入「chat」可以跟機器人聊天。\n隨時輸入「fsm」可以得到當下的狀態圖。')
                machine.go_back()
            elif machine.state == 'user':
                send_text_message(event.reply_token, '輸入「menu」即可進入主選單。\n隨時輸入「chat」可以跟機器人聊天。\n隨時輸入「fsm」可以得到當下的狀態圖。')
            elif machine.state == 'menu':
                send_text_message(event.reply_token, '輸入「weather」查看天氣。\n輸入「tour」規劃旅程')
            elif machine.state == 'enterPosition': 
                send_text_message(event.reply_token, '請輸入景點關鍵字')
            elif machine.state == 'choosePosition':
                send_text_message(event.reply_token, '請選擇定位所在地')
            elif machine.state == 'positioning': 
                send_text_message(event.reply_token, '請傳送位置訊息')
            elif machine.state == 'preference':
                send_text_message(event.reply_token, '輸入旅程的偏好')
            elif machine.state == 'chooseRoute':
                send_text_message(event.reply_token, '選擇旅程')
                
    return 'OK'


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw('fsm.png', prog='dot', format='png')
    return send_file('fsm.png', mimetype='image/png')


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
