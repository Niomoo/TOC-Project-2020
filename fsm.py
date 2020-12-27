from transitions.extensions import GraphMachine
from utils import send_text_message, send_carousel_message, send_button_message, send_image_message
import requests
from linebot.models import ImageCarouselColumn, URITemplateAction, MessageTemplateAction
import pymysql
import numpy as np
import pandas as pd
from math import radians, cos, sin, asin, sqrt
import copy
import random
import json
import urllib.request
import time

# 連接資料庫
conn = pymysql.connect(host="remotemysql.com", port=3306, user="7laUVxPtp9", password="JBjmPdUTTM",db="7laUVxPtp9")
cursor = conn.cursor()
try:
    print("Connection")
except:
    print("Connection failed")

# 抓DB資料存成list或dict
cursor.execute("select * from attraction")
res = cursor.fetchall()
attraction = pd.DataFrame(list(res))
cursor.execute("select * from mrt")
res = cursor.fetchall()
mrt = pd.DataFrame(list(res))
cursor.execute("select * from arelated")
res = cursor.fetchall()
arelated = pd.DataFrame(list(res))
cursor.execute("select * from mrelated")
res = cursor.fetchall()
mrelated = pd.DataFrame(list(res))
cursor.execute("select * from tags")
res = cursor.fetchall()
tags = pd.DataFrame(list(res))

attraction.set_index(attraction[0], drop=True, inplace=True)
attraction = attraction.to_dict(orient='index')
mrt.set_index(mrt[0], drop=True, inplace=True)
mrt = mrt.to_dict(orient='index')
arelated = arelated.values
mrelated = mrelated.values
tags = tags.values

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_menu(self, event):
        text = event.message.text
        return text.lower() == "menu"

    def is_going_to_weather(self, event):
        text = event.message.text
        return text.lower() == "查看天氣"

    def is_going_to_planTour(self, event):
        text = event.message.text
        return text.lower() == "規劃旅程"

    def is_going_to_choosePosition(self, event):
        text = event.message.text
        return text.lower() == "定位所在地"

    def is_going_to_positioning(self, event):
        location = event.message.location
        lng = event.message.longitude
        lat = event.message.latitude
        return location.lower() == location

    def is_going_to_enterPosition(self, event):
        text = event.message.text
        return text.lower() == "輸入出發地"

    def is_going_to_preference(self, event):
        text = event.message.text
        return text.lower() == "選擇旅程偏好"

    def on_enter_menu(self, event):
        print("this is menu")
        title = '主選單'
        text = '選擇「查看天氣」或「規劃旅程」'
        btn = [
            MessageTemplateAction(
                label='查看天氣',
                text='查看天氣'
            ),
            MessageTemplateAction(
                label='規劃旅程',
                text='規劃旅程'
            ),
        ]
        url='https://miro.medium.com/max/2732/1*tQYvg76G0vvov4Qsjt0klg.jpeg'
        reply_token = event.reply_token
        send_button_message(reply_token, title, text, btn, url)
        
    def on_enter_weather(self, event):
        print("check weather")
        reply_token = event.reply_token
        send_text_message(reply_token, "最近有點冷，要注意保暖喔")
        self.go_back_menu(event)

    def on_enter_planTour(self, event):
        print("let's plan tour")
        title = '高雄旅程規劃'
        text = '選擇「定位所在地」或「輸入出發地」'
        btn = [
            MessageTemplateAction(
                label='定位所在地',
                text='定位所在地'
            ),
            MessageTemplateAction(
                label='輸入出發地',
                text='輸入出發地'
            ),
        ]
        url='https://www.flaticon.com/svg/static/icons/svg/854/854878.svg'
        reply_token = event.reply_token
        send_button_message(reply_token, title, text, btn, url)

    def on_enter_choosePosition(self, event):
        print("Positioning")
        reply_token = event.reply_token
        send_text_message(reply_token, "請傳送位置訊息")

    def on_enter_positioning(self, event):
        # lng = event.message.longitude
        # lat = event.message.latitude
        # minDist = 10000
        # minId = 1
        # for i in attraction:
        #     d = haversine(float(lng), float(lat), attraction[i][6], attraction[i][5])
        #     if d < minDist:
        #         minDist = d
        #         minId = i
        # departure = attraction[minId][1]
        print("departure")
        reply_token = event.reply_token
        send_text_message(reply_token, "藍屋-日式料理")
        
    def on_enter_enterPosition(self, event):
        print("Enter Position")

    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r

    def findAllViewpoints(userInput):
        if userInput == "":
            return "noInput"
        viewList = {}
        mrtViewList = {}
        allJson = {}
        count = 0
        num = cursor.execute("select aId,aName from attraction where aName like '%" + userInput + "%'")
        res = cursor.fetchall()
        if num != 0:
            for (row1,row2) in res:
                viewList[row1] = row2
        num = cursor.execute("select * from mrt where mName like '%" + userInput + "%'")
        res = cursor.fetchall()
        if num != 0:
            for (m,n,near) in res:
                mrtViewList[near] = n
        if len(viewList) == 0 and len(mrtViewList) == 0:
            return "noPoint"
        for i in viewList:
            viewJson = {}
            viewJson['id'] = i
            viewJson['name'] = viewList[i]
            viewJson['type'] = 0
            allJson[count] = viewJson
            count += 1
        for i in mrtViewList:
            viewJson = {}
            viewJson['id'] = i
            viewJson['name'] = mrtViewList[i]
            viewJson['type'] = 1
            allJson[count] = viewJson
            count += 1
        return json.dumps(allJson)

    def text(view, attraction, arelated, aList, aWeight, isTag, allList):
        b = 0
        # 非第一個景點，可能需要關聯
        if len(view) > 1: 
            tmp = []
            for i in arelated:
                if int(i[2]) == view[len(view)-1]:
                    tmp.append(i[1])
            for i in arelated:
                if (int(i[2]) == view[len(view)-2]) and (i[1] in tmp) and (int(i[3]) in isTag) and (int(i[3]) not in allList) and (int(i[3]) not in view):
                    aList[int(i[3])] = i[6]
                    b = 1
        if b == 0:
            for i in arelated:
                if (int(i[2]) == view[len(view)-1]) and (int(i[3]) in isTag) and (int(i[3]) not in allList) and (int(i[3]) not in view):
                    aList[int(i[3])] = i[6]
        
        # 計算view[0]跟aList景點的距離
        for i in aList:
            dist = haversine(attraction[view[len(view)-1]][6], attraction[view[len(view)-1]][5], attraction[i][6], attraction[i][5])
            if dist != 0:
                aList[i] = (1/dist) * aList[i] * aWeight * attraction[i][9]

    def nearby(view, attraction, aList, dWeight, isTag, mList, allList):
        nearMrt = attraction[view[len(view)-1]][7]
        mList.append(nearMrt)
        for i in attraction:
            if (attraction[i][7] == nearMrt) and (i not in allList) and (i not in view)  and (i in isTag):
                dist = haversine(attraction[view[len(view)-1]][6], attraction[view[len(view)-1]][5], attraction[i][6], attraction[i][5])
                if dist != 0:
                    if i in aList:
                        aList[i] = aList[i] + (1/dist) * dWeight * attraction[i][9]
                    else:
                        aList[i] = (1/dist) * dWeight * attraction[i][9]

    def data(view, attraction, mrelated, aList, mWeight, isTag, mList, isMrt, allList):
        b = 0
        nextMrt = {}
        # 前一個景點來自可能三，可能需要關聯
        if len(mList) > 1: 
            tmp = []
            for i in mrelated:
                if i[2] == mList[len(mList)-1]:
                    tmp.append(i[1])
            for i in mrelated:
                if (i[2] == mList[0]) and (i[1] in tmp) and (i[3] not in mList):
                    nextMrt[int(i[3])] = i[6]
                    b = 1
        if b == 0:
            for i in mrelated:
                if (i[2] == mList[len(mList)-1]) and (i[3] not in mList):
                    nextMrt[int(i[3])] = i[6]
        
        # 關聯後捷運站的附近景點
        for i in nextMrt:
            for j in attraction:
                if (attraction[j][7] == i) and (j not in allList) and (j not in view) and (j in isTag):
                    isMrt[j] = i
                    # 景點間的距離用經緯度計算
                    dist = haversine(attraction[view[len(view)-1]][6], attraction[view[len(view)-1]][5], attraction[j][6], attraction[j][5])
                    # 距離用景點跟捷運站間的距離計算
                    if dist != 0:
                        if j in aList:
                            aList[j] = aList[j] + (1/dist) * nextMrt[i] * mWeight * attraction[j][9]
                        else:
                            aList[j] = (1/dist) * nextMrt[i] * mWeight * attraction[j][9]

    def firstRecommend():
        start = request.args.get('start')
        inputTags = request.args.get('inputTags')
        isType = request.args.get('isType')
        mList = []              #紀錄計算過程中有用到的捷運站
        view = []               #暫存上一個點
        aList = {}              #暫存景點結果（景點id+加權後分數）
        route = []              #回傳所有路線
        allList = []
        tmpTag = []
        idName = [[] for i in range(5)]
        start = int(start)
        isType = int(isType)
        if isType == 1:
            for i in mrt:
                if mrt[i][2] == start:
                    mrtName = mrt[i][1]
                    break
            if len(result[0]) > 0:
                for i in range(5):
                    result[i][0] = mrtName
                    resId[i][0] = start
                    while len(result[i]) > 3:
                        del result[i][len(result[i])-1]
            else:
                for i in range(5):
                    result[i].append(mrtName)
                    resId[i].append(start)
        else:
            if len(result[0]) > 0:
                for i in range(5):
                    result[i][0] = attraction[start][1]
                    resId[i][0] = start
                    while len(result[i]) > 3:
                        del result[i][len(result[i])-1]
            else:
                for i in range(5):               #第一層景點（使用者輸入的）
                    result[i].append(attraction[start][1])
                    resId[i].append(start)
        allList.append(start)
        tag = [n for n in inputTags.split()] #記錄所有tag
        if len(tag) != 0:                    #有輸入tag
            for i in tags:
                if i[2] in tag:
                    tmpTag.append(i[1])
        else:                                #沒有指定tag，故所有景點都會考慮
            for i in attraction:
                tmpTag.append(i)
        
        idx = 0
        if len(tmpTag) < len(isTag):
            while idx != len(tmpTag):
                isTag[idx] = tmpTag[idx]
                idx = idx + 1
            for i in range(idx, len(isTag), 1):
                del isTag[len(isTag)-1]
        elif len(tmpTag) > len(isTag):
            while idx != len(isTag):
                isTag[idx] = tmpTag[idx]
                idx = idx + 1
            for i in range(idx, len(tmpTag), 1):
                isTag.append(tmpTag[i])
        else:
            for i in range(0, len(isTag), 1):
                isTag[i] = tmpTag[i]

        # 計算每條路線的第二個點
        view.append(start)
        
        text(view, attraction, arelated, aList, aWeight, isTag, allList)
        nearby(view, attraction, aList, dWeight, isTag, mList, allList)
        data(view, attraction, mrelated, aList, mWeight, isTag, mList, isMrt, allList)
        resList = sorted(aList.items(), key=lambda item: item[1], reverse=True)
        copyOfmList = copy.copy(mList)

        for i in range(5):
            if len(resList) > i and len(result[i]) > 1:
                result[i][1] = attraction[resList[i][0]][1]
                resId[i][1] = resList[i][0]
                allList.append(resList[i][0])
            elif len(resList) > i:
                result[i].append(attraction[resList[i][0]][1])
                resId[i].append(resList[i][0])
                allList.append(resList[i][0])

        # 計算每條路線的第三個點
        for i in range(5):
            view = []
            aList = {}
            view.append(start)
            if len(resList) > i:
                view.append(resList[i][0])
                mList = copy.copy(copyOfmList)
                if resList[i][0] in isMrt:
                    mList.append(isMrt[resList[i][0]])

                text(view, attraction, arelated, aList, aWeight, isTag, allList)
                nearby(view, attraction, aList, dWeight, isTag, mList, allList)
                data(view, attraction, mrelated, aList, mWeight, isTag, mList, isMrt, allList)

            if len(aList) != 0:
                maxScore = max(aList, key=aList.get)
                if len(result[i]) > 2:
                    result[i][2] = attraction[maxScore][1]
                    resId[i][2] = maxScore
                else:
                    result[i].append(attraction[maxScore][1])
                    resId[i].append(maxScore)
                allList.append(maxScore)
            if len(result[i]) > 1:
                if isType == 1:
                    tmp = str(resId[i][0]) + "@" + result[i][0] + "@" + str(1)
                else:
                    tmp = str(resId[i][0]) + "@" + result[i][0] + "@" + str(0)
                idName[i].append(tmp)
                for n in range(1, len(result[i]), 1):
                    tmp = str(resId[i][n]) + "@" + result[i][n] + "@" + str(0)
                    idName[i].append(tmp)
                tmpStr = ">".join(idName[i])
                route.append(tmpStr)
            else:
                route.append("查無景點路線")
        routeStr = ",".join(route)
        return str(routeStr)

    def findAddress():
        routeId = request.args.get('Id')
        routeId = int(routeId)
        address = []
        for i in resId[routeId]:
            address.append(attraction[i][2])
        resAddress = ">".join(address)
        return resAddress

    def pointDetail():
        aId = request.args.get('aId')
        aId = int(aId)
        detail = []
        detail.append(attraction[aId][2])
        detail.append(str(attraction[aId][3]))
        detail.append(str(attraction[aId][4]))
        resDetail = ">".join(detail)
        return str(resDetail)

    GOOGLE_API_KEY = 'AIzaSyD1oQOM90IDt-hyKm-vKI9f4X2c_AAm-kY'

    def get_latitude_longtitude(address):
        # decode url
        address = urllib.request.quote(address)
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + address + '&key=' + GOOGLE_API_KEY
        
        while True:
            res = requests.get(url)
            js = json.loads(res.text)

            if js["status"] != "OVER_QUERY_LIMIT":
                time.sleep(1)
                break

        result = js["results"][0]["geometry"]["location"]
        lat = result["lat"]
        lng = result["lng"]
        print(lat,lng)
        return lat, lng

    # 隨輸入更改之參數
    userInput = "高雄車站"       #使用者輸入關鍵字找出最近景點
    lng = float(125)        #定位使用者經度
    lat = float(23)         #定位使用者緯度
    start = 1293            #起始景點id
    inputTags = "自然風景"   #選擇tag
    aWeight = 0.2           #文字關聯權重
    dWeight = 0.5           #距離計算權重
    mWeight = 0.3           #捷運關聯權重
    changeIndex = 0         #以result第1筆作為更改範例
    change = 2              #1->替換第二個點；2->替換第三個點
    addIndex = 0            #以result第一筆作為更改範例

    # 變數宣告
    result = [[] for i in range(5)]      #紀錄最後路線結果
    resId = [[] for i in range(5)]       #紀錄最後路線結果id
    idName = [[] for i in range(5)]      #id+名字
    allList = []                         #記錄景點id（判斷用）
    isTag = []                           #紀錄符合tag的景點們
    copyOfmList = []                     #紀錄最初捷運站（跑後面的路線會用到）
    resList = []                         #暫存排序後的結果
    isMrt = {}                           #暫存如果是來自可能三的結果（會影響到mList）
