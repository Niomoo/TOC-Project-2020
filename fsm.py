from transitions.extensions import GraphMachine
from utils import send_text_message, send_carousel_message, send_button_message, send_image_message
import requests
from linebot.models import ImageCarouselColumn, URITemplateAction, MessageTemplateAction

global departure
departure = '駁二藝術特區'


class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_menu(self, event):
        text = event.message.text
        return text.lower() == "menu"

    def on_enter_menu(self, event):
        print("this is menu")
        title = '主選單'
        text = '選擇「查看天氣」或「規劃旅程」'
        btn = [
            MessageTemplateAction(
                label='查看天氣',
                text='weather'
            ),
            MessageTemplateAction(
                label='規劃旅程',
                text='tour'
            ),
        ]
        url = 'https://miro.medium.com/max/2732/1*tQYvg76G0vvov4Qsjt0klg.jpeg'
        reply_token = event.reply_token
        send_button_message(reply_token, title, text, btn, url)

    def is_going_to_weather(self, event):
        text = event.message.text
        return text.lower() == "weather"

    def on_enter_weather(self, event):
        print("check weather")
        reply_token = event.reply_token
        send_text_message(reply_token, "最近有點冷，要注意保暖喔")
        self.go_back_menu(event)

    def is_going_to_planTour(self, event):
        text = event.message.text
        return text.lower() == "tour"

    def on_enter_planTour(self, event):
        print("let's plan tour")
        title = '高雄旅程規劃'
        text = '選擇「定位所在地」或「輸入出發地」'
        btn = [
            MessageTemplateAction(
                label='定位所在地',
                text='藍屋-日式料理'
            ),
            MessageTemplateAction(
                label='輸入出發地',
                text='駁二藝術特區'
            ),
        ]
        url = 'https://www.flaticon.com/svg/static/icons/svg/854/854878.svg'
        reply_token = event.reply_token
        send_button_message(reply_token, title, text, btn, url)

    def is_going_to_preference(self, event):
        text = event.message.text
        # if text.lower() == '定位所在地':
        #     departure = '藍屋-日式料理'
        # elif text.lower() == '輸入出發地':
        #     departure = '駁二藝術特區'
        # reply_token = event.reply_token
        # send_text_message(reply_token, str(departure))
        # text2 = event.message.text
        return text.lower() == '駁二藝術特區'

    def on_enter_preference(self, event):
        print("Preference")
        title = '高雄旅程規劃'
        text = '選擇此趟旅程偏好'
        btn = [
            MessageTemplateAction(
                label='美食小吃',
                text='美食小吃'
            ),
            MessageTemplateAction(
                label='自然風景',
                text='自然風景'
            ),
            MessageTemplateAction(
                label='歷史古蹟',
                text='歷史古蹟'
            ),
            MessageTemplateAction(
                label='藝術文化',
                text='藝術文化'
            ),
        ]
        url = 'https://www.flaticon.com/svg/static/icons/svg/1483/1483151.svg'
        reply_token = event.reply_token
        send_button_message(reply_token, title, text, btn, url)

    def is_going_to_chooseRoute(self, event):
        global pref
        text = event.message.text
        if text == '美食小吃' or text == '歷史古蹟' or text == '藝術文化' or text == '自然風景':
            pref = text
            return True
        return False

    def on_enter_chooseRoute(self, event):
        print("chooseRoute")
        if event.message.text.lower() == '美食小吃':
            text = '還敢吃啊'
            send_text_message(event.reply_token, text)
        elif event.message.text.lower() == '自然風景':
            text = '好漂亮'
            send_text_message(event.reply_token, text)
        elif event.message.text.lower() == '歷史古蹟':
            text = '讚讚'
            send_text_message(event.reply_token, text)
        elif event.message.text.lower() == '藝術文化':
            text = '文青'
            send_text_message(event.reply_token, text)
        self.go_back_menu(event)


        # def is_going_to_choosePosition(self, event):
        #     text = event.message.text
        #     return text.lower() == "定位所在地"

        # def is_going_to_positioning(self, event):
        #     location = event.message.location
        #     lng = event.message.location.longitude
        #     lat = event.message.location.latitude
        #     minDist = 10000
        #     minId = 1
        #     for i in attraction:
        #         d = haversine(float(lng), float(lat), attraction[i][6], attraction[i][5])
        #         if d < minDist:
        #             minDist = d
        #             minId = i
        #     departure = attraction[minId][1]
        #     return text.lower() == "departure"

        # def is_going_to_enterPosition(self, event):
        #     text = event.message.text
        #     return text.lower() == "輸入出發地"

        # def is_going_to_inputPosition(self, event):
        #     text = event.message.text

        # def on_enter_choosePosition(self, event):
        #     print("Positioning")
        #     reply_token = event.reply_token
        #     send_text_message(reply_token, "請傳送位置訊息")

        # def on_enter_positioning(self, event):
        #     print("departure")
        #     reply_token = event.reply_token
        #     send_text_message(reply_token, "藍屋-日式料理")

        # def on_enter_enterPosition(self, event):
        #     print("Enter Position")
        #     reply_token = event.reply_token
        #     send_text_message(reply_token, "請輸入景點關鍵字")

        # def on_enter_inputPosition(self, event):
        #     print("Input Position")
