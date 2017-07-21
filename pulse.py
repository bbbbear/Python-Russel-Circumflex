import spidev
import time
import numpy as np
from bbearClass import PULSEIBI, BOOL, RAWPULSE
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

def pulsePNN(spi_ch,adc_ch,threadRun,IBI, rawpulse):
    #log = open("log-new-design3-plt.csv","w")
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
    ignoreMax = 5

    #SPI initialization
    spi = spidev.SpiDev()
    spi.open(0,spi_ch)
    spi.max_speed_hz = 1200000
    lastBeatTime = datetime.now()
    start = lastBeatTime

    hthres_timer = 0

    while threadRun:
        signal = get_adc(spi,adc_ch)

        #log.write(str(signal)+'\n')
        now = datetime.now()
        timePeriod = int((now - lastBeatTime).total_seconds()*1000)
        #log.write(str((now - start).total_seconds()*1000)+','+str(signal)+'\n')
        rawpulse.put(signal)
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
    #                log.write(','+str(signal)+',0')
                    #print 'New through: ',through

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
    #                    log.write(','+str(threshold)+','+str(amplitude)+'\n')
                        time.sleep(0.0018)
                        #print 'First beat'
            #            log.write('\n')
                        continue
                    else:
                        IBI.put(newIBI)

        #threshold adustment, wait for a falling edge then ask for the peak recorded
        if signal < threshold and pulse:
            pulse = False
            amplitude = peak-through
            if amplitude < 350 and peak < 600:
                print 'No pulse detected, reset', amplitude, peak, through, threshold
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
            #log.write(','+str(signal)+'\n')
            print ('RESET')
        time.sleep(0.0018)
    print ('Exiting pulse sensor reader')
    spi.close()
    #log.close()
    return
#    log.close()
