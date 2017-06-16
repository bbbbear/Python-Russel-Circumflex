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


newFlag = False



threadRun = THREADRUN()


def getSignal(mindwaveDataPointReader,cond,threadRun,queue, IBI):
    global newFlag
    count = 0
    while(threadRun.status()):
        dataPoint = mindwaveDataPointReader.readNextDataPoint()
        if(dataPoint.__class__ is AttentionDataPoint):
            #print 'AT:',dataPoint.value()
            attention = dataPoint.value()
            count += 1
        elif(dataPoint.__class__ is MeditationDataPoint):
            meditaton = dataPoint.value()
            #print 'MD:',dataPoint.value()
            count += 1
        elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
            poorSignal = dataPoint.value()
            #print 'POOR:',dataPoint.value()
            count += 1
        #If all of 3 inputs come
        if (count == 3):
            count = 0
            cond.acquire()
            queue.put([poorSignal,meditaton,attention,IBI.BPM(), IBI.pNNx()])
            newFlag = True
            cond.notify()
            cond.release()
            #print 'data:', attention, meditaton, poorSignal
            #time.sleep(0.2)
    print ("Exiting mind wave reader")
    return

def main():
    global newFlag
    global threadRun
    IBI = PULSEIBI()
    queue = QUEUE()

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
            pl = threading.Thread(target=pulse.pulsePNN,name="Pulse sensor reader",args=(0, 0, threadRun, IBI))
            pl.daemon = True
            pl.start()
            ThreadStarted = 1
            print ("Reading pulse sensor thread is started")
            try:
                mv = threading.Thread(target=getSignal,name="mind wave reader",args=(mindwaveDataPointReader,bv_condition,threadRun, queue,IBI))
                mv.daemon = True
                mv.start()
                ThreadStarted = 2
                print ("Reading mind wave thread is started")
                #Tflag = True

            except:
                e = sys.exc_info()[0]
                print ("Can not start the mind wave reader thread",e)
                threadRun.stop()
                return
        except:
            e = sys.exc_info()[0]
            print ("Can not start the pulse sensor reader thread",e)
            threadRun.stop()
            return

        while threadRun.status():
            #Critical section
            bv_condition.acquire()
            while not newFlag:
                bv_condition.wait()
            print queue.getAll()
            #print "data:", attention, meditaton, poorSignal, pulse.pNN50, pulse.BPM, "\tDifftime: ", (now-prev).total_seconds()
            newFlag = False
            bv_condition.release()
            #End of Critical section
            #The computation unit starts here!


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
