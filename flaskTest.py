#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# 引入模組
import pymysql
import numpy as np
import pandas as pd
from math import radians, cos, sin, asin, sqrt
import copy
import random
from flask import Flask
from flask_cors import CORS
from flask import request
import json
from utils import POOL

app = Flask(__name__)
CORS(app)

# 連接資料庫
# conn = pymysql.connect(host="remotemysql.com", port=3306, user="7laUVxPtp9", password="JBjmPdUTTM",db="7laUVxPtp9")
# cursor = conn.cursor()
try:
    conn = POOL.connection()
    cursor = conn.cursor()
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

@app.route('/')
def hollo():
    return "hello flask"

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

@app.route('/findAllViewpoint', methods=['GET'])
def findAllViewpoints():
    userInput = request.args.get('userInput')
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

@app.route('/findNearestViewpoint', methods=['GET'])
def findNearestViewpoint():
    lng = request.args.get('lng')
    lat = request.args.get('lat')
    minDist = 10000
    minId = 1
    for i in attraction:
        d = haversine(float(lng), float(lat), attraction[i][6], attraction[i][5])
        if d < minDist:
            minDist = d
            minId = i
    resNear = str(minId) + "@" + attraction[minId][1]
    return str(resNear)

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

@app.route('/firstRecommend', methods=['GET'])
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

@app.route('/findAddress', methods=['GET'])
def findAddress():
    routeId = request.args.get('Id')
    routeId = int(routeId)
    address = []
    for i in resId[routeId]:
        address.append(attraction[i][2])
    resAddress = ">".join(address)
    return resAddress


def changeTheSecond(resId, index, view, aList, maxDist):
    # 可能一（文字關聯）
    tmp = []
    tmp1 = []
    for i in arelated:
        if int(i[2]) == view[0]:
            tmp1.append(i[1])
        if (int(i[3]) == view[1]) and (i[1] in tmp1):
            tmp.append(i[1])
    for i in arelated:
        if (i[1] in tmp) and (int(i[2]) in isTag) and (int(i[2]) not in view):
            aList[int(i[2])] = i[6]
    
    for i in aList:
        dist = haversine(attraction[view[0]][6], attraction[view[0]][5], attraction[i][6], attraction[i][5])
        if (dist != 0) and (dist <= maxDist):
            aList[i] = (1/dist) * aList[i] * aWeight * attraction[i][9]
    
    # 可能二（距離最近捷運站附近之景點）
    nearMrt1 = attraction[view[0]][7]
    for i in attraction:
        if (attraction[i][7] == nearMrt1) and (i not in view)  and (i in isTag):
            dist = haversine(attraction[view[0]][6], attraction[view[0]][5], attraction[i][6], attraction[i][5])
            if (dist != 0) and (dist <= maxDist):
                if i in aList:
                    aList[i] = aList[i] + (1/dist) * dWeight * attraction[i][9]
                else:
                    aList[i] = (1/dist) * dWeight * attraction[i][9]
                   
    # 可能三（捷運關聯）
    nearMrt2 = attraction[view[1]][7]
    tmp2 = []
    tmp3 = [] 
    nextMrt = {}
    for i in mrelated:
        if i[2] == nearMrt1:
            tmp2.append(i[1])
        if (i[3] == nearMrt2) and (i[1] in tmp2):
            tmp3.append(i[1])
    for i in mrelated:
        if (i[1] in tmp3) and (i[2] != nearMrt1):
            nextMrt[int(i[2])] = i[6]
    
    for i in nextMrt:
        for j in attraction:
            if (attraction[j][7] == i) and (j not in view) and (j in isTag):
                dist = haversine(attraction[view[0]][6], attraction[view[0]][5], attraction[j][6], attraction[j][5])
                if (dist != 0) and (dist <= maxDist):
                    if j in aList:
                        aList[j] = aList[j] + (1/dist) * nextMrt[i] * mWeight * attraction[j][9]
                    else:
                        aList[j] = (1/dist) * nextMrt[i] * mWeight * attraction[j][9]
    
    # 選擇更換景點
    if resId[index][1] in aList:
        del aList[resId[index][1]]
    if len(aList) == 0:
        print("沒有更好的景點了！")
        print(result[index])
    else:
        aNew, scoreNew = random.choice(list(aList.items()))
        resId[index][1] = aNew                    
        result[index][1] = attraction[aNew][1]
        print(attraction[aNew][1])
        print(result[index])
        
def changeTheLast(resId, index, view, aList, mList):
    text(view, attraction, arelated, aList, aWeight, isTag, allList)
    nearby(view, attraction, aList, dWeight, isTag, mList, allList)
    data(view, attraction, mrelated, aList, mWeight, isTag, mList, isMrt, allList)
    
    if resId[index][2] in aList:
        del aList[resId[index][2]]
    if len(aList) == 0:
        print("沒有更好的景點了！")
        print(result[index])
    else:
        # 隨機取本次計算的值，只會跟上次不一樣，多次嘗試下來可能換到重覆景點
        aNew, scoreNew = random.choice(list(aList.items()))
        resId[index][2] = aNew                  #紀錄新景點id                    
        result[index][2] = attraction[aNew][1]  #紀錄新景點名稱
        print(attraction[aNew][1])              #印出更新後的景點
        print(result[index])                    #印出更新後的該條路線
        
@app.route('/changePoint', methods=['GET'])
def changePoint():
    print(len(isTag))

    changeIndex = request.args.get('changeIndex')
    change = request.args.get('change')
    index = int(changeIndex)
    change = int(change)
    view = []
    mList = []
    aList = {}
    view.append(resId[index][0])
    if change == 1:
        view.append(resId[index][2])
        maxDist = haversine(attraction[view[0]][6], attraction[view[0]][5], attraction[view[1]][6], attraction[view[1]][5])
        changeTheSecond(resId, index, view, aList, maxDist)
        anotherPoint = str(resId[index][1]) + "," + result[index][1] + "," + str(0)
        return str(anotherPoint)
    elif change == 2:
        view.append(resId[index][1])
        changeTheLast(resId, index, view, aList, mList)
        anotherPoint = str(resId[index][2]) + "," + result[index][2] + "," + str(0)
        return str(anotherPoint)

@app.route('/addPoint', methods=['GET'])
def addPoint():
    addIndex = request.args.get('addIndex')
    index = int(addIndex)
    mList = []
    aList = {}
    allChoice = []

    text(resId[index], attraction, arelated, aList, aWeight, isTag, allList)
    nearby(resId[index], attraction, aList, dWeight, isTag, mList, allList)
    data(resId[index], attraction, mrelated, aList, mWeight, isTag, mList, isMrt, allList)

    if len(aList) == 0:
        print(result[index])
        return "沒有更好的景點了！"
    elif len(resId[index]) < 6:
        for i in aList:
            tmpStr = str(i) + "," + attraction[i][1] + "," + str(0)
            allChoice.append(tmpStr)
        resChoice = ">".join(allChoice)
        return str(resChoice)    #所有可新增的路線
    else:
        print(result[index])
        return "已達景點數上限！"

@app.route('/verifyAddPoint', methods=['GET'])
def verifyAddPoint():
    routeIdx= request.args.get('routeIdx')
    idx= request.args.get('idx')
    isMrt= request.args.get('isMrt')
    routeIdx = int(routeIdx)
    idx = int(idx)
    result[routeIdx].append(attraction[idx][1])
    resId[routeIdx].append(idx)
    resRoute = str(len(result[routeIdx]))
    resRoute += "~"
    resRoute += (str(resId[routeIdx][0]) + "@false@" + result[routeIdx][0] + "@" + str(isMrt) + ">")
    for i in range(1, len(result[routeIdx]), 1):
        if i < len(result[routeIdx]) - 1:
            resRoute += (str(resId[routeIdx][i]) + "@false@" + result[routeIdx][i] + "@" + str(0) + ">")
        else:
            resRoute += (str(resId[routeIdx][i]) + "@true@" + result[routeIdx][i] + "@" + str(0))
    return str(resRoute)

@app.route('/pointDetail', methods=['GET'])
def pointDetail():
    aId = request.args.get('aId')
    aId = int(aId)
    detail = []
    detail.append(attraction[aId][2])
    detail.append(str(attraction[aId][3]))
    detail.append(str(attraction[aId][4]))
    resDetail = ">".join(detail)
    return str(resDetail)

@app.route('/changeOrAddAddress', methods=['GET'])
def changeOrAddAddress():
    routeIdx = request.args.get('routeIdx')
    pointIdx = request.args.get('pointIdx')
    routeIdx = int(routeIdx)
    pointIdx = int(pointIdx)
    newId = resId[routeIdx][pointIdx]
    newAddress = attraction[newId][2]
    return str(newAddress)

@app.route('/addPointAddress', methods=['GET'])
def addPointAddress():
    aId = request.args.get('aId')
    aId = int(aId)
    newAddress = attraction[aId][2]
    return str(newAddress)

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

if __name__ == "__main__":
    app.run()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




