import time
import bluetooth
from mindwavemobile.MindwaveDataPoints import RawDataPoint, AttentionDataPoint, MeditationDataPoint, PoorSignalLevelDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
import textwrap
import threading
import sys
import os
import pulse
import signal
from datetime import datetime
from bbearClass import QUEUE, PULSEIBI, THREADRUN
import numpy as np


attention = None
meditaton = None
poorSignal = None
newFlag = False



threadRun = THREADRUN()


def getSignal(mindwaveDataPointReader,cond,threadRun, IBI):
    global attention
    global meditaton
    global poorSignal
    global newFlag
    count = 0
    while(threadRun.status()):
        dataPoint = mindwaveDataPointReader.readNextDataPoint()
        if(dataPoint.__class__ is AttentionDataPoint):
            #print 'AT:',dataPoint.value()
            tmp_attention = dataPoint.value()
            count += 1
        elif(dataPoint.__class__ is MeditationDataPoint):
            tmp_meditaton = dataPoint.value()
            #print 'MD:',dataPoint.value()
            count += 1
        elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
            tmp_poorSignal = dataPoint.value()
            #print 'POOR:',dataPoint.value()
            count += 1
        if (count == 3):
            count = 0
            cond.acquire()
            meditaton = tmp_meditaton
            attention = tmp_attention
            poorSignal = tmp_poorSignal
            newFlag = True
            cond.notify()
            cond.release()
            #print 'data:', attention, meditaton, poorSignal
            #time.sleep(0.2)
    print ("Exiting mind wave reader")
    return

def main():
    global attention
    global meditaton
    global poorSignal
    global newFlag
    global threadRun
    IBI = PULSEIBI()

    bv_condition = threading.Condition()
    #Try to connect to the predefined device
    print "Main program is started on PID", os.getpid()
    mindwaveDataPointReader = MindwaveDataPointReader("20:68:9D:3F:4F:88")
    mindwaveDataPointReader.start()
    if(not mindwaveDataPointReader.isConnected()):
        print ("Find another device...")
        mindwaveDataPointReader = MindwaveDataPointReader()
        mindwaveDataPointReader.start()
    ThreadStarted = 0
    if (mindwaveDataPointReader.isConnected()):
        try:
            pl = threading.Thread(target=pulse.pulsePNN,name="Pulse sensor reader",args=(0,0,threadRun, IBI))
            pl.daemon = True
            pl.start()
            ThreadStarted = 1
            print ("Reading pulse sensor thread is started")
            try:
                mv = threading.Thread(target=getSignal,name="mind wave reader",args=(mindwaveDataPointReader,bv_condition,threadRun, IBI))
                mv.daemon = True
                mv.start()
                ThreadStarted = 2
                print ("Reading mind wave thread is started")
                #Tflag = True

            except:
                e = sys.exc_info()[0]
                print ("Can not start the mind wave reader thread",e)
                threadRun.stop()
        except:
            e = sys.exc_info()[0]
            print ("Can not start the pulse sensor reader thread",e)
            threadRun.stop()
        prev = datetime.now()
        while threadRun.status():
            bv_condition.acquire()
            if newFlag:
                #mutex.acquire()
                now = datetime.now()
                print "data:", attention, meditaton, poorSignal, pulse.pNN50, pulse.BPM, "\tDifftime: ", (now-prev).total_seconds()
                newFlag = False
                prev = now
                #mutex.release()
                #time.sleep(0.5)
            else:
                bv_condition.wait()
            bv_condition.release()
        if ThreadStarted == 1:
            if pl.isAlive():
                pl.join(5)
            print ("Child thread are successfully closed")
        elif ThreadStarted == 2:
            if pl.isAlive():
                pl.join(5)
            if mv.isAlive():
                mv.join(5)
            print ("Child thread are successfully closed")
        sys.exit(0)

def handler(signal, frame):
    global threadRun
    print ("\nCtrl-C... Entering exiting precedure")
    threadRun.stop()
    #Tflag = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main()



'''
if __name__ == '__main__':
    #Try to connect to the predefined device
    mindwaveDataPointReader = MindwaveDataPointReader("20:68:9D:3F:4F:88")
    mindwaveDataPointReader.start()

    #If the predefined device can't be connected, try any on discovery mode
    if(not mindwaveDataPointReader.isConnected()):
        print 'Find another device...'
        mindwaveDataPointReader = MindwaveDataPointReader()
        mindwaveDataPointReader.start()
    else:
        print("Connected to predefined device")
    if (mindwaveDataPointReader.isConnected()):
        while(True):
            dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if(dataPoint.__class__ is AttentionDataPoint):
                print 'AT:',dataPoint.value()
            elif(dataPoint.__class__ is MeditationDataPoint):
                print 'MD:',dataPoint.value()
            elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
                print 'POOR:',dataPoint.value()

    else:
        print(textwrap.dedent("""\
            Exiting because the program could not connect
            to the Mindwave Mobile device.""").replace("\n", " "))'''
