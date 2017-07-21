import serial
import time
import numpy as np
from bbearClass import PULSEIBI
from datetime import datetime
import os


def pulsePNN(threadRun,IBI,tty,baudrate):
    #The peak and through will be used for finding the amplitude of a pulse wave
    peak = 600      #peak of the pulse wave
    through = 600   #lowest value of the pulse wave
    amplitude = 600
    threshold = 600 #The threshold of acceptable pulse wave
    newIBI = 0
    pulse = False
    ignoredBeat = False
    ignoredCount = 0 #Ignored 10 beats
    ignoreMax = 5

    #Serial initialization
    try:
        port = serial.Serial(tty,baudrate)
    except:
        print 'Serial initialization failed, kill the program'
        os.kill(os.getpid,9)
    lastBeatTime = datetime.now()
    start = lastBeatTime

    hthres_timer = 0
    #log = open('pulselog.csv','w')
    port.flushInput()
    for i in range(0,70):
        port.readline()
    while threadRun:
        try:
            signal = int(port.readline())
        except:
            continue
        now = datetime.now()
        #log.write(str((now - start).total_seconds()*1000)+','+str(signal)+'\n')
        timePeriod = int((now - lastBeatTime).total_seconds()*1000)
        if signal > 1000:
            hthres_timer += 2.2
            if hthres_timer > 800:
                hthres_timer = 0
                resetFlag = True

        resetFlag = False
        if(signal > peak):
            #signal is greather than threshold, trying to update the peak
            peak = signal

        #avoiding dicrotic notch by waiting 60% of last IBI
        if (timePeriod > newIBI*0.6):
            #updating the peak and the through of a signal
            if(signal < threshold):
                #signal is lower than threshold, trying to update the through
                if (signal < through):
                    through = signal

            #waiting for at least 250ms before determinding the pulse wave to avoid the noise
            if timePeriod > 250:
                if (signal > threshold) and not pulse:
                    newIBI = timePeriod
                    lastBeatTime = now

                    if ignoredBeat:
                        if ignoredCount <= ignoreMax:
                            ignoredCount += 1
                        else:
                            ignoredBeat = False
                        continue
                    else:
                        IBI.put(newIBI)

        #threshold adustment, wait for a falling edge then ask for the peak recorded
        if signal < threshold and pulse:
            pulse = False
            amplitude = peak-through
            if amplitude < 350 and peak < 600:
                #print 'No pulse detected, reset', amplitude, peak, through, threshold
                resetFlag = True
            else:
                threshold = (amplitude*0.6) + through
                peak = threshold
                through = threshold
        #if there is no beats in 2.5 seconds, reset the threshold by the default value
        if timePeriod > 2500 or resetFlag:
            threshold = 600
            peak = 600
            through = 600
            amplitude = 600
            lastBeatTime = now
            ignoredBeat = True
            ignoredCount = 0
            ignoreMax = 2
            newIBI = 600
            IBI.reset()
            #print ('RESET')
        #time.sleep(0.0018)
    #print ('Exiting pulse sensor reader')
    #log.close()
    return
