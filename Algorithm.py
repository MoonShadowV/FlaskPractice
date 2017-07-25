# -*- coding: utf-8 -*
import pandas as pd
import math
import multiprocessing

ProLock = multiprocessing.Lock()#进程IO互斥锁
Sim = pd.Series()

def Algorithm(videoData,userData):#算法主体部分
    # videoData 视频数据,DataFrame类型
    # userData 用户偏好表,Series类型

    videoIndex = videoData.ix[:,2:8]#视频热度数据
    videoAid = videoData["aid"]#视频的Aid
    videoTag = videoData.ix[:,8:-1]#视频标签
    videoNum = videoData.__len__()#视频数量
    videoValue = videoData.ix[:, -1]

    similarity = {}#余弦相似度度量，字典类型，key为视频aid

    userPrefVictor = mod(userData)#用户偏好向量的模值


    for i in range(videoNum):
        videoVictor = pd.Series(data=1,index=videoTag.iloc[i].dropna().values)#构造视频向量
        dot = (videoVictor * userData).dropna().sum()#计算内积
        similarity[videoAid.iloc[i]] = dot / (videoValue.iloc[i]+userPrefVictor)#余弦相似度

    similarity = pd.Series(similarity)
    #互斥，以便进行IO操作
    ProLock.acquire()
    # path = "F:\WorkPlace\Python\Bilibili_Alogrithm\similarity.csv"
    # similarity.to_csv(path,mode='a+')
    global Sim
    Sim = Sim.append(similarity)
    ProLock.release()


#取模运算
def mod(data):
    sum = 0
    length = len(data)
    for i in range(length):
        sum  += data[i]**2
    return math.sqrt(sum)


def runAlgorithm(Data,userData):
    #对数据分片，以便多进程
    data1 = Data[:100000]
    data2 = Data[100000:200000]
    data3 = Data[200000:300000]
    data4 = Data[300000:400000]
    data5 = Data[400000:]

    #多进程
    C1 = multiprocessing.Process(target=Algorithm,args=(data1,userData))
    C1.start()

    C2 = multiprocessing.Process(target=Algorithm, args=(data2, userData))
    C2.start()

    C3 = multiprocessing.Process(target=Algorithm, args=(data3, userData))
    C3.start()

    C4 = multiprocessing.Process(target=Algorithm, args=(data4, userData))
    C4.start()

    C5 = multiprocessing.Process(target=Algorithm, args=(data5, userData))
    C5.start()
    C5.join()

    return Sim

