#!/usr/bin/env python
from __future__ import print_function

import time
import bluetooth
from mindwavemobile.MindwaveDataPoints import RawDataPoint, AttentionDataPoint, MeditationDataPoint, PoorSignalLevelDataPoint, EEGPowersDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
import threading
import multiprocessing
import pulse
import signal
import os, sys
from datetime import datetime
from bbearClass import *
import numpy as np
#from the merging of Tanaka's work
import matplotlib
import matplotlib.pyplot as plt
import math
import time


threadRun = BOOL()
ctype_threadRun = multiprocessing.Value('i',1)


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
            count = 1
        elif(dataPoint.__class__ is AttentionDataPoint):
            attention = dataPoint.value()
            count = 2
        elif(dataPoint.__class__ is EEGPowersDataPoint):
            EEG_Power = dataPoint.value()
            count = 3
        elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
            poorSignal = dataPoint.value()
            count = 4
        #If all of 3 inputs come
        if (count == 4):
            count = 0
            #print ('\n\t\tP-Trying to lock')
            with cond:
            #cond.acquire()
            #    print ('\n\t\tP-LOCK')
                count = 0
                queue.put([poorSignal,attention,meditaton,EEG_Power,IBI.pNNx()])
                newFlag.true()
                cond.notify()
            time.sleep(0.4)
            #    print ('\n\t\tP-NOTI')
            #print ('\n\t\tP-RELE')
            #cond.release()
            #print 'data:', attention, meditaton, poorSignal
            #time.emotion[7](0.2)
    with cond:
        cond.notify()
        print ("Exiting mind wave reader")
        return

def handle_close(evt):
    print('Closed Figure!, Sending interrupt signal')
    os.kill(os.getppid(), signal.SIGINT)

def plotGraph(ctype_threadRun,multi_cond,ctype_percent_emotion, ctype_oneMinEmo,ctype_rawpulse,ctype_rawpulse_label,ctype_bpm):
    print('Hello plotGraph')
    #Graph initialization
    plt.ion()
    plt.style.use('ggplot')
    font = {'family' : 'Monospace'}
    matplotlib.rc('font', **font)
    fig, (ax1,ax2,ax3) = plt.subplots(3,sharex=False, figsize=(20,10))
    fig.canvas.mpl_connect('close_event', handle_close)

    emoGraph = ax1.bar(range(8), np.zeros((8)), align='center')
    oneMinEmoGraph = ax2.bar(range(8), np.zeros((8)), align='center')
    #plt.title(('Emotion Estimation'))
    ax1.set_title('Overall Emotion Estimation')
    ax1.set_xticklabels(('','pleasure','excite','arouse','distress','misery','depress','sleep','content'))
    ax1.set_xlabel('moods')
    ax1.set_ylabel('estimated moods(%)')
    ax1.set_ylim([0,100])
    ax2.set_title('Lastest 1 Minute Emotion Estimation')
    ax2.set_xticklabels(('','pleasure','excite','arouse','distress','misery','depress','sleep','content'))
    ax2.set_xlabel('moods')
    ax2.set_ylabel('estimated moods(%)')
    ax2.set_ylim([0,100])

    ax3.set_title('Pulse sensor graph')
    ax3.set_xlabel('time')
    ax3.set_ylabel('signal')
    ax3.set_ylim([0,1023])
    ax3.set_xlim([-3, 0])
    pulse_range = ctype_rawpulse_label[:]
    pulseWave = ax3.plot(pulse_range,ctype_rawpulse[:])
    pulseWave[0].set_xdata(pulse_range)
    bpm = ctype_bpm.value
    if bpm == 0:
        str_bpm = '-- BPM'
    else:
        str_bpm = str(bpm)+' BPM'
    t1 = ax3.text(0, 800,  str_bpm, fontsize=14)

    plt.subplots_adjust(hspace=1.2)
    fig.canvas.draw()
    plt.pause(0.00001)


    while ctype_threadRun.value:
        with multi_cond:
            try:
                multi_cond.wait(2)
            except:
                print('Timed out, update graph')
                rawpulse = ctype_rawpulse[:]
                fig.canvas.draw()
                plt.pause(0.00001)
                continue

            percent_emotion = ctype_percent_emotion[:]
            oneMinEmo = ctype_oneMinEmo[:]
            rawpulse = ctype_rawpulse[:]

        #plot the graph
        for emog, data in zip(emoGraph,percent_emotion):
            emog.set_height(data)

        for emog, data in zip(oneMinEmoGraph,oneMinEmo):
            emog.set_height(data)

        #Plot the pulse graph
        pulseWave[0].set_ydata(rawpulse)

        bpm = ctype_bpm.value
        if bpm == 0:
            str_bpm = '-- BPM'
        else:
            str_bpm = str(bpm)+' BPM'
        t1.set_text(str_bpm)

        #Commit the change in graph
        fig.canvas.draw()
        plt.pause(0.00001)
    '''if not os.path.exists('./lastshot'):
        os.makedirs('./lastshot')
    plt.savefig('./lastshot/lastshot'+"{:%d-%m-%Y_%H-%M-%S}".format(datetime.now())+'.png')'''
    print('Exiting plotting process')
    return




def main():

    #Default setting
    macaddr = ""
    spi_ch = 0
    sensor_ch = 0
    pNNx = 50
    npNN = 30
    nBPM = 10
    #Load configuration file
    try:
        settingFile = open("setting.txt","r")
        print('Fond setting file')
        tmp = settingFile.readlines()
        settingFile.close()
        for line in tmp:
            line = line.strip()
            if line[0] == '#' or line[0] == '':
                continue
            else:
                cmd = line.split(':')
                if cmd[0].lower() == 'macaddr':
                    macaddr = cmd[1].strip()
                elif cmd[0].lower() == 'spi-ch':
                    spi_ch = int(cmd[1].strip())
                elif cmd[0].lower() == 'pulse-ch':
                    sensor_ch = int(cmd[1].strip())
                elif cmd[0].lower() == 'pnnx':
                    pNNx = int(cmd[1].strip())
                elif cmd[0].lower() == 'n-pnnx':
                    npNN = int(cmd[1].strip())
                elif cmd[0].lower() == 'n-bpm':
                    nBPM = int(cmd[1].strip())
                else:
                    print('Unknown setting',cmd[0])
    except:
        print('File not found, use default setting')


    newFlag = BOOL(False)
    global threadRun
    IBI = PULSEIBI(size=npNN, pNNx=pNNx)
    queue = QUEUE()
    rawpulse = RAWPULSE(length=3,diff = -0.002)
    rawpulse_size = rawpulse.size()
    ThreadStarted = 0

    raw_emotion = np.zeros((8)) #[happy,excite,surprise,strain,sad,ennui,calm,sleep] -> 'pleasure','excite','arouse','distress','misery','depress','sleep','content'
    percent_emotion = [0]*8
    percent_min_emotion = [0]*8

    #Prepare for multiprocessing, plot graph
    global ctype_threadRun
    ctype_percent_emotion = multiprocessing.Array('d',[0]*8)
    ctype_oneMinEmo = multiprocessing.Array('d',[0]*8)
    ctype_rawpulse = multiprocessing.Array('i',[0]*rawpulse_size)
    ctype_rawpulse_label = multiprocessing.Array('d',rawpulse.label())
    bpm = IBI.BPM()
    if bpm is None:
        ctype_bpm = multiprocessing.Value('i',0)
    else:
        ctype_bpm = multiprocessing.Value('i',bpm)
    multi_cond = multiprocessing.Condition()

    bv_condition = threading.Condition()
    #Try to connect to the predefined device
    print ("Main program is started on PID", os.getpid())
    try:
        pl = threading.Thread(target=pulse.pulsePNN,name="Pulse sensor reader",args=(spi_ch, sensor_ch, threadRun, IBI, rawpulse))
        pl.daemon = True
        pl.start()
        ThreadStarted = 1
        print ("Reading pulse sensor thread is started")
    except:
        e = sys.exc_info()[0]
        print ("Can not start the pulse sensor reader thread",e)
        threadRun.stop()
        ctype_threadRun.value = 0
        return

    try:
        pt = multiprocessing.Process(target=plotGraph,name="Graph plotter",args=(ctype_threadRun,multi_cond,ctype_percent_emotion, ctype_oneMinEmo,ctype_rawpulse,ctype_rawpulse_label,ctype_bpm))
        pt.daemon = True
        pt.start()
        ThreadStarted = 2
        print ("Plotting process is started")
        #Tflag = True
    except:
        e = sys.exc_info()[0]
        print ("Can not start the plotting process",e)
        threadRun.stop()
        ctype_threadRun.value = 0
        return

    if macaddr != '':
        mindwaveDataPointReader = MindwaveDataPointReader("20:68:9D:3F:4F:88")
        mindwaveDataPointReader.start()
        if(not mindwaveDataPointReader.isConnected()):
            print ("Find another device...")
            mindwaveDataPointReader = MindwaveDataPointReader()
            mindwaveDataPointReader.start()
    else:
        print ("Searching for device")
        mindwaveDataPointReader = MindwaveDataPointReader()
        mindwaveDataPointReader.start()

    if (mindwaveDataPointReader.isConnected()):
        print('Connected to',mindwaveDataPointReader.mac())
        try:
            mv = threading.Thread(target=getSignal,name="mind wave reader",args=(mindwaveDataPointReader,bv_condition,threadRun, newFlag,queue,IBI))
            mv.daemon = True
            mv.start()
            ThreadStarted = 3
            print ("Reading mind wave thread is started!")
            #Tflag = True
        except:
            e = sys.exc_info()[0]
            print ("Can not start the mind wave reader thread",e)
            threadRun.stop()
            ctype_threadRun.value = 0
            return


        #while threadRun.status():
        start = datetime.now()
        oneMinEmo = CIR_ARRAY(60)
        this_emotion = np.empty((8))

        while threadRun:
            #Critical section
            with bv_condition:
            #bv_condition.acquire()
                while not newFlag:
                    bv_condition.wait()
                    if not threadRun:
                        break
                #print queue.getAll()
                qData = queue.getAll()
                #[poorSignal,meditaton,attention,BPM,pNN50]
                now = datetime.now()
                newFlag.false()
            #print('QLEN:',len(qData))
            #print ('\n\tC-RELE')
            #bv_condition.release()
            #End of Critical section
            #The computation unit starts here!
            updateFlag = False
            for data in qData:
                if data[4] is not None and data[0] < 50:
                    arousal = data[1] - data[2]   #Equivalent to kakusei in Tanaka's work
                    updateFlag = True
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

                    # OLD 'happy','excite','surprise','strain','sad','ennui','calm','sleep'
                    # NEW 'pleasure','excite','arouse','distress','misery','depress','sleep','content'
                    #emotion classification
                    this_emotion[:] = 0
                    '''
                    if angle < 45:
                        #angle between 0 - 44
                        raw_emotion[0] += 1
                        raw_emotion[1] += 1

                        this_emotion[0] += 1
                        this_emotion[1] += 1
                    elif angle < 90:
                        #angle between 45 - 89
                        raw_emotion[2] += 1
                        raw_emotion[1] += 1

                        this_emotion[2] += 1
                        this_emotion[1] += 1
                    elif angle < 135:
                        #angle between 90 - 134
                        raw_emotion[2] += 1
                        raw_emotion[3] += 1

                        this_emotion[2] += 1
                        this_emotion[3] += 1
                    elif angle < 180:
                        #angle between 135 - 179
                        raw_emotion[4] += 1
                        raw_emotion[3] += 1

                        this_emotion[4] += 1
                        this_emotion[3] += 1
                    elif angle < 225:
                        #angle between 180 - 224
                        raw_emotion[4] += 1
                        raw_emotion[5] += 1

                        this_emotion[4] += 1
                        this_emotion[5] += 1
                    elif angle < 270:
                        #angle between 225 - 269
                        raw_emotion[7] += 1
                        raw_emotion[5] += 1

                        this_emotion[7] += 1
                        this_emotion[5] += 1
                    elif angle < 315:
                        #angle between 270 - 314
                        raw_emotion[7] += 1
                        raw_emotion[6] += 1

                        this_emotion[7] += 1
                        this_emotion[6] += 1
                    else:
                        #angle between 315 - 359
                        raw_emotion[0] += 1
                        raw_emotion[6] += 1

                        this_emotion[0] += 1
                        this_emotion[6] += 1
                    '''
                    if angle < 45:
                        #pleasure - excite
                        #angle between 0 - 44
                        emotionB = angle/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[0] += emotionA
                        raw_emotion[1] += emotionB

                        this_emotion[0] += emotionA
                        this_emotion[1] += emotionB
                    elif angle < 90:
                        #excite - arouse
                        #angle between 45 - 89
                        emotionB = (angle - 45.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[1] += emotionA
                        raw_emotion[2] += emotionB

                        this_emotion[1] += emotionA
                        this_emotion[2] += emotionB
                    elif angle < 135:
                        #arouse - distress
                        #angle between 90 - 134
                        emotionB = (angle - 90.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[2] += emotionA
                        raw_emotion[3] += emotionB

                        this_emotion[2] += emotionA
                        this_emotion[3] += emotionB
                    elif angle < 180:
                        #distress - misery
                        #angle between 135 - 179
                        emotionB = (angle - 135.0)/45.0
                        emotionA = 1 - emotionB


                        raw_emotion[3] += emotionA
                        raw_emotion[4] += emotionB

                        this_emotion[3] += emotionA
                        this_emotion[4] += emotionB
                    elif angle < 225:
                        #misery - depress
                        #angle between 180 - 224
                        emotionB = (angle - 180.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[4] += emotionA
                        raw_emotion[5] += emotionB

                        this_emotion[4] += emotionA
                        this_emotion[5] += emotionB
                    elif angle < 270:
                        #depress - sleep
                        #angle between 225 - 269
                        emotionB = (angle - 225.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[5] += emotionA
                        raw_emotion[6] += emotionB

                        this_emotion[5] += emotionA
                        this_emotion[6] += emotionB
                    elif angle < 315:
                        #sleep - content
                        #angle between 270 - 314
                        emotionB = (angle - 270.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[6] += emotionA
                        raw_emotion[7] += emotionB

                        this_emotion[6] += emotionA
                        this_emotion[7] += emotionB
                    else:
                        #content - pleasure
                        #angle between 315 - 360
                        emotionB = (angle - 315.0)/45.0
                        emotionA = 1 - emotionB

                        raw_emotion[7] += emotionA
                        raw_emotion[0] += emotionB

                        this_emotion[7] += emotionA
                        this_emotion[0] += emotionB
                    print ('emotion: ',raw_emotion, round(data[4],2), angle)
                    oneMinEmo.put(this_emotion)
                else:
                    oneMinEmo.put([0,0,0,0,0,0,0,0])

            #Updating the graph
            if updateFlag:
                #Calculate the graph
                raw_sum = raw_emotion.sum()
                if raw_sum != 0:
                    percent_emotion[:] = raw_emotion*(100/raw_emotion.sum())
                else:
                    percent_emotion[:] = [0]*8

            #Calculate the one min graph
            oneMin = oneMinEmo.get()
            oneMin_raw = np.array([sum(x) for x in zip(*oneMin)])
            oneMin_sum = sum(oneMin_raw)
            if oneMin_sum != 0:
                factor = 100.0/oneMin_sum
                percent_min_emotion[:] = oneMin_raw*(100.0/oneMin_sum)
            else:
                percent_min_emotion[:] = [0]*8

            with multi_cond:
                ctype_percent_emotion[:] = percent_emotion
                ctype_oneMinEmo[:] = percent_min_emotion
                ctype_rawpulse[:] = rawpulse.get()
                bpm = IBI.BPM(nBPM)
                if bpm is None:
                    ctype_bpm.value = 0
                else:
                    ctype_bpm.value = int(round(bpm))
                multi_cond.notify()

    with multi_cond:
        multi_cond.notify()
    mindwaveDataPointReader.close()
    if ThreadStarted == 1:
        if pl.is_alive():
            pl.join(5)
        print ("1 Child thread are successfully closed")
    elif ThreadStarted == 2:
        if pl.is_alive():
            pl.join(5)
        if pt.is_alive():
            pt.join(5)
        print ("2 Child thread are successfully closed")
    elif ThreadStarted == 3:
        if pl.is_alive():
            pl.join(5)
        if mv.is_alive():
            mv.join(5)
        if pt.is_alive():
            pt.join(10)
        print ("3 Child thread are successfully closed")
    sys.exit(0)

def handler(signal, frame):
    global threadRun
    global ctype_threadRun
    print ("\nCtrl-C... Entering exiting precedure")
    threadRun.false()
    ctype_threadRun.value = 0
    #threadRun = False
    #Tflag = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main()
