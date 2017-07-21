from __future__ import print_function
import time
import bluetooth
from mindwavemobile.MindwaveDataPoints import EEGPowersDataPoint, RawDataPoint, AttentionDataPoint, MeditationDataPoint, PoorSignalLevelDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
import textwrap
from datetime import datetime

if __name__ == '__main__':
    #Try to connect to the predefined device
    mindwaveDataPointReader = MindwaveDataPointReader('20:68:9D:3F:4F:88')
    mindwaveDataPointReader.start()

    #If the predefined device can't be connected, try any on discovery mode
    if(not mindwaveDataPointReader.isConnected()):
        mindwaveDataPointReader = MindwaveDataPointReader()
        mindwaveDataPointReader.start()
    else:
        print('Connected to predefined device')
    count = 0
    tnum = 0
    if (mindwaveDataPointReader.isConnected()):
        start = datetime.now()
        while(True):
            '''dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if (not dataPoint.__class__ is RawDataPoint):
                print count,'-----------------------------------------------'
                print dataPoint
                print 'type', type(dataPoint), dataPoint.__class__
                print '-----------------------------------------------'''
            dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if(dataPoint.__class__ is AttentionDataPoint):
                att = dataPoint.value()
                count = 1
            elif(dataPoint.__class__ is MeditationDataPoint):
                med = dataPoint.value()
                count = 2
            elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
                poor = dataPoint.value()
                count = 4
#                time.sleep(0.2)
            elif(dataPoint.__class__ is EEGPowersDataPoint):
                count = 3
                eeg = dataPoint.value()

            else:
                print('.',end = '')
            if count == 4:
                count = 0
                tnum += 1
                now = datetime.now()
                print('\n','#',tnum,'->',att,med,eeg,poor,'>',now-start,now)
            #count += 1
    else:
        print(textwrap.dedent("""\
            Exiting because the program could not connect
            to the Mindwave Mobile device.""").replace("\n", " "))
