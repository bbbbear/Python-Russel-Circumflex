import spidev
import time
import numpy as np
from bbearClass import PULSEIBI, THREADRUN
from datetime import datetime

BPM = None
pNN50 = None

def get_adc(spi,channel):
    # Only 2 channels 0 and 1 else return -1
    if ((channel > 1) or (channel < 0)):
            return -1

    # Send start bit, sgl/diff, odd/sign, MSBF
    # channel = 0 sends 0000 0001 1000 0000 0000 0000
    # channel = 1 sends 0000 0001 1100 0000 0000 0000
    # sgl/diff = 1; odd/sign = channel; MSBF = 0
    r = spi.xfer2([1,(2+channel)<<6,0])
    #r = spi.xfer2([(2+channel)<<6,0])

    # spi.xfer2 returns same number of 8 bit bytes
    # as sent. In this case, 3 - 8 bit bytes are returned
    # We must then parse out the correct 10 bit byte from
    # the 24 bits returned. The following line discards
    # all bits but the 10 data bits from the center of
    # the last 2 bytes: XXXX XXXX - XXXX DDDD - DDDD DDXX
    # r[1] DDDX XXXX & 0001 1111 -> 0XXX XX00 0000
    # r[2] XXXX XXDD             ->      00XX XXXX
    # r[1] + r[2]                -> 0XXX XXXX XXXX
    # Still unclear but the result is correct
    ret = ((r[1]&31) << 6) + (r[2] >> 2)
    return ret

def pulsePNN(spi_ch,adc_ch,threadRun,IBI):
    #log = open("log.csv","w")
    #log.write('Actual,Raw,Low,Peak,IBI UPDATE,threshold,amplitude\n')
    #lastBeatTime = 0
    #The peak and through will be used for finding the amplitude of a pulse wave
    peak = 600      #peak of the pulse wave
    through = 600   #lowest value of the pulse wave
    amplitude = 600
    threshold = 600 #The threshold of acceptable pulse wave
    newIBI = 0
    pulse = False
    ignoredBeat = False
    ignoredCount = 0 #Ignored 10 beats

    #SPI initialization
    spi = spidev.SpiDev()
    spi.open(0,spi_ch)
    spi.max_speed_hz = 1200000
    lastBeatTime = datetime.now()
    while threadRun.status():
        signal = get_adc(spi,adc_ch)
        now = datetime.now()
        timePeriod = int((now - lastBeatTime).total_seconds()*1000)
    #    log.write(str(timePeriod)+','+str(signal))
        #print 'Raw',signal
        #N = timerCounter - lastBeatTime
        flag_1 = False
        flag_2 = False
        resetFlag = False
        if(signal > peak):
            #signal is greather than threshold, trying to update the peak
            peak = signal
    #        log.write(',0,'+str(signal))
            flag_1 = True

        #avoiding dicrotic notch by waiting 60% of last IBI
        if (timePeriod > newIBI*0.6):
            #updating the peak and the through of a signal
            if(signal < threshold):
                #signal is lower than threshold, trying to update the through
                if (signal < through):
                    through = signal
    #                log.write(','+str(signal)+',0')
                    flag_1 = True
                    #print 'New through: ',through

            #waiting for at least 250ms before determinding the pulse wave to avoid the noise
            if timePeriod > 250:
                if (signal > threshold) and not pulse:
                    pulse = True
                    flag_2 = True
                    newIBI = timePeriod
                    lastBeatTime = now
    #                if flag_1:
    #                    log.write(','+str(signal))
    #                else:
    #                    log.write(',,,'+str(signal))

                    if ignoredBeat:
                        if ignoredCount <= 10:
                            ignoredCount += 1
                        else:
                            ignoredBeat = False
    #                    log.write(','+str(threshold)+','+str(amplitude)+'\n')
                        time.sleep(0.002)
                        #print 'First beat'
                        continue
                    else:
                        IBI.put(newIBI)

        #threshold adustment, wait for a falling edge then ask for the peak recorded
        if signal < threshold and pulse:
            pulse = False
            amplitude = peak-through
            if amplitude < 250 and peak < 600:
                print 'No pulse detected, reset'
                resetFlag = True
            else:
                threshold = (amplitude/2.0) + through
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
            newIBI = 600
            IBI.reset()
            print ('RESET')
    #    if not flag_1:
    #        log.write(',,')
    #    if not flag_2:
    #        log.write(',')
    #    log.write(','+str(threshold)+','+str(amplitude)+'\n')
#        log.write('\n')
        IBI_prev = newIBI
        time.sleep(0.002)
    print ('Exiting pulse sensor reader')
    spi.close()
    #log.close()
    return
#    log.close()
