import time
import bluetooth
from mindwavemobile.MindwaveDataPoints import RawDataPoint, AttentionDataPoint, MeditationDataPoint, PoorSignalLevelDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
import textwrap

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
    if (mindwaveDataPointReader.isConnected()):
        while(True):
            '''dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if (not dataPoint.__class__ is RawDataPoint):
                print count,'-----------------------------------------------'
                print dataPoint
                print 'type', type(dataPoint), dataPoint.__class__
                print '-----------------------------------------------'''
            dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if(dataPoint.__class__ is AttentionDataPoint):
                print dataPoint
            elif(dataPoint.__class__ is MeditationDataPoint):
                print dataPoint
            elif(dataPoint.__class__ is PoorSignalLevelDataPoint):
                print dataPoint
            elif(dataPoint.__class__ is not RawDataPoint):
                print 'else: ', dataPoint.__class__
            #count += 1
    else:
        print(textwrap.dedent("""\
            Exiting because the program could not connect
            to the Mindwave Mobile device.""").replace("\n", " "))
