#!/usr/bin/env python
from __future__ import print_function

import time
import bluetooth
from mindwavemobile.MindwaveDataPoints import RawDataPoint, AttentionDataPoint, MeditationDataPoint, PoorSignalLevelDataPoint, EEGPowersDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
import threading
import pulse

import os, sys
from datetime import datetime
from bbearClass import *
import numpy as np
#from the merging of Tanaka's work
import math

#threadRun = True

def getSignal(mindwaveDataPointReader,cond,threadRun,newFlag,queue, IBI):
    #global threadRun
    count = 0
    #while(threadRun.status()):
    while(threadRun):
        #print ('{[P-GET]',tcount,'}:', end='')
        dataPoint = mindwaveDataPointReader.readNextDataPoint()
            #print ('b', end='')
        if(dataPoint.__class__ is MeditationDataPoint):
            meditaton = dataPoint.value()
            #print 'MD:',dataPoint.value()
            count = 1
        elif(dataPoint.__class__ is AttentionDataPoint):
            #print 'AT:',dataPoint.value()
            attention = dataPoint.value()
            count = 2
        elif(dataPoint.__class__ is EEGPowersDataPoint):
            EEG_Power = dataPoint.value()
            count = 3
        elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
            poorSignal = dataPoint.value()
            #print 'POOR:',dataPoint.value()
            count = 4

        if (count == 4):
            count = 0
            with cond:
            #cond.acquire()
            #    print ('\n\t\tP-LOCK')
                queue.put([poorSignal,attention,meditaton,EEG_Power,IBI.pNNx(),IBI.BPM()])
                newFlag.true()
                cond.notify()
            #cond.release()
            #print 'data:', attention, meditaton, poorSignal
            #time.emotion[7](0.2)
    with cond:
        cond.notify()
    #print ("Exiting mind wave reader")
    return


def russell_fn(emotion,threadRun,mac_addr,tty,baudrate,IBI):
    newFlag = BOOL(False)
    queue = QUEUE()

    bv_condition = threading.Condition()
    #Try to connect to the predefined device
    #print ("Russell program is started on PID", os.getpid())
    try:
        pl = threading.Thread(target=pulse.pulsePNN,name="Pulse sensor reader",args=(threadRun, IBI, tty, baudrate))
        pl.daemon = True
        pl.start()
        ThreadStarted = 1
        #print ("Reading pulse sensor thread is started")
    except:
        e = sys.exc_info()[0]
        #print ("Can not start the pulse sensor reader thread",e)
        threadRun.stop()
        return

    if mac_addr != '':
        mindwaveDataPointReader = MindwaveDataPointReader(mac_addr)
        mindwaveDataPointReader.start()
        if(not mindwaveDataPointReader.isConnected()):
            print ("Find another device...")
            mindwaveDataPointReader = MindwaveDataPointReader()
            mindwaveDataPointReader.start()
    else:
        mindwaveDataPointReader = MindwaveDataPointReader()
        mindwaveDataPointReader.start()
    ThreadStarted = 0

    if (mindwaveDataPointReader.isConnected()):
        print('Connected to',mindwaveDataPointReader.macaddr())
        try:
            mv = threading.Thread(target=getSignal,name="mind wave reader",args=(mindwaveDataPointReader,bv_condition,threadRun, newFlag,queue,IBI))
            mv.daemon = True
            mv.start()
            ThreadStarted = 2
            #print ("Reading mind wave thread is started")
            #Tflag = True
        except:
            e = sys.exc_info()[0]
            #print ("Can not start the mind wave reader thread",e)
            threadRun.stop()
            return

        start = datetime.now()
        #oneMinEmo = CIR_ARRAY(60)
        this_emotion = np.empty((8))
        while threadRun:
            #Critical section
            with bv_condition:
                while not newFlag:
                    bv_condition.wait()
                    if not threadRun:
                        break
                qData = queue.getAll()
                now = datetime.now()
                newFlag.false()

            #End of Critical section
            #The computation unit starts here!
            for data in qData:
                if data[4] is not None and data[5] is not None and data[0] < 50:
                    arousal = data[1] - data[2]   #Equivalent to kakusei in Tanaka's work
                    if data[4] < 0.3:
                        pleasure = -100*(data[4]/0.3)
                    else:
                        pleasure = 100*(data[4]-0.3)/0.7
                    angle = math.degrees(math.atan2(arousal,pleasure))

                    if angle < 0:
                        angle += 360
                    elif angle >= 360:
                        angle -= 360

                    if angle < 0 or angle > 360:
                        print ('Unexpected error on angle, stopping for 10 seconds')
                        time.sleep(10)

                    #'happy','excite','surprise','strain','sad','ennui','calm','sleep'
                    #emotion classification
                    this_emotion[:] = 0
                    if angle < 45:
                        #pleasure - excite
                        #angle between 0 - 44
                        emotionB = angle/45.0
                        emotionA = 1 - emotionB

                        this_emotion[0] += emotionA
                        this_emotion[1] += emotionB
                    elif angle < 90:
                        #excite - arouse
                        #angle between 45 - 89
                        emotionB = (angle - 45.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[1] += emotionA
                        this_emotion[2] += emotionB
                    elif angle < 135:
                        #arouse - distress
                        #angle between 90 - 134
                        emotionB = (angle - 90.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[2] += emotionA
                        this_emotion[3] += emotionB
                    elif angle < 180:
                        #distress - misery
                        #angle between 135 - 179
                        emotionB = (angle - 135.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[3] += emotionA
                        this_emotion[4] += emotionB
                    elif angle < 225:
                        #misery - depress
                        #angle between 180 - 224
                        emotionB = (angle - 180.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[4] += emotionA
                        this_emotion[5] += emotionB
                    elif angle < 270:
                        #depress - sleep
                        #angle between 225 - 269
                        emotionB = (angle - 225.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[5] += emotionA
                        this_emotion[6] += emotionB
                    elif angle < 315:
                        #sleep - content
                        #angle between 270 - 314
                        emotionB = (angle - 270.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[6] += emotionA
                        this_emotion[7] += emotionB
                    else:
                        #content - pleasure
                        #angle between 315 - 360
                        emotionB = (angle - 315.0)/45.0
                        emotionA = 1 - emotionB

                        this_emotion[7] += emotionA
                        this_emotion[0] += emotionB
                    #oneMinEmo.put(this_emotion)
                    emotion.addAll(this_emotion)
                else:
                    emotion.addAll([0]*8)
        mindwaveDataPointReader.close()
        if ThreadStarted == 1:
            if pl.isAlive():
                pl.join(5)
            #print ("Child thread are successfully closed")
        elif ThreadStarted == 2:
            if pl.isAlive():
                pl.join(5)
            if mv.isAlive():
                mv.join(5)
            #print ("Child thread are successfully closed")
        sys.exit(0)
    else:
        print('Error, can not connect to a mindwave device')
        if ThreadStarted == 1:
            if pl.isAlive():
                pl.join(5)
            #print ("Child thread are successfully closed")
        elif ThreadStarted == 2:
            if pl.isAlive():
                pl.join(5)
            if mv.isAlive():
                mv.join(5)
        os.kill(os.getpid(),9)
        sys.exit(0)


class russell():
    def __init__(self,mac_addr='',tty='',baudrate=0,pNNx=0,npNN=0,nBPM=0,scope=0,settingFile="setting.txt",useSettingFile=False):
        if useSettingFile:
            try:
                setting = open(settingFile,"r")
                tmp = setting.readlines()
                setting.close()
            except:
                print('File not found, use defined-default setting')
                if baudrate == 0:
                    baudrate = 115200
                if pNNx == 0:
                    pNNx = 50
                if npNN == 0:
                    npNN = 30
                if nBPM == 0:
                    self.__nBPM = 10
                if scope == 0:
                    scope = 60
            properties = [False]*7
            for line in tmp:
                line = line.strip()
                if not line:
                    continue
                if line[0] == '#':
                    continue
                else:
                    cmd = line.split(':')
                    if cmd[0].lower() == 'macaddr':
                        f_macaddr = cmd[1].strip()
                        properties[0] = True
                    elif cmd[0].lower() == 'tty':
                        f_tty = cmd[1].strip()
                        properties[1] = True
                    elif cmd[0].lower() == 'baudrate':
                        f_baudrate = int(cmd[1].strip())
                        properties[2] = True
                    elif cmd[0].lower() == 'pnnx':
                        f_pNNx = int(cmd[1].strip())
                        properties[3] = True
                    elif cmd[0].lower() == 'n-pnnx':
                        f_npNN = int(cmd[1].strip())
                        properties[4] = True
                    elif cmd[0].lower() == 'n-bpm':
                        f_nBPM = int(cmd[1].strip())
                        properties[5] = True
                    elif cmd[0].lower() == 'scope-sec':
                        f_scope = int(cmd[1].strip())
                        properties[6] = True

                    else:
                        print('Unknown keyword',cmd[0])

                if properties[0]:
                    if macaddr == '':
                        mac_addr = f_macaddr
                if properties[1]:
                    if tty == '':
                        tty = f_tty
                if properties[2]:
                    if baudrate == 0:
                        baudrate = f_baudrate
                else:
                    baudrate = 115200
                if properties[3]:
                    if pNNx == 0:
                        pNNx = f_pNNx
                else:
                    pNNx = 50
                if properties[4]:
                    if npNN == 0:
                        npNN = f_npNN
                else:
                    npNN = 30
                if properties[5]:
                    if nBPM == 0:
                        self.__nBPM = f_nBPM
                    else:
                        self.__nBPM = nBPM
                else:
                    self.__nBPM = 10
                if properties[6]:
                    if scope == 0:
                        scope = f_scope
                else:
                    scope = 60

        else:
            if baudrate == 0:
                baudrate = 115200
            if pNNx == 0:
                pNNx = 50
            if npNN == 0:
                npNN = 30
            if nBPM == 0:
                self.__nBPM = 10
            if scope == 0:
                scope = 60
        self.__emotion = EMOTION(scope)
        self.__threadRun = BOOL()
        self.__IBI = PULSEIBI(size=npNN,pNNx = pNNx)
        if tty == '':
            print('API error, no serial tty')
            os.kill(os.getpid(),9)
        try:
            self.__worker = threading.Thread(target=russell_fn,name="russell-worker",args=(self.__emotion,self.__threadRun,mac_addr,tty,baudrate,self.__IBI))
            self.__worker.daemon = True
            self.__worker.start()
            ThreadStarted = True
            #Tflag = True
        except:
            e = sys.exc_info()[0]
            print ("Can not start the mind wave reader thread",e)
            return

    def stop(self):
        self.__threadRun.false()
        self.__worker.join(10)

    def bpm(self):
        return self.__IBI.BPM(self.__nBPM)

    def IBI(self):
        return self.__IBI.pNNx()

    def getAllPercent(self,reader=True):
        return self.__emotion.getAllPercent(readed)

    def getScopePercent(self,readed=True):
        return self.__emotion.getScopePercent(readed)

    def isUpdate(self):
        return self.__emotion.isUpdate()
