#!/usr/bin/env python
from __future__ import print_function
import time
from api.russell import russell
import signal


def handler(signal, frame):
    global emotion
    global run
    print ("\nCtrl-C... Entering exiting precedure")
    emotion.stop()
    run = False
    #threadRun = False
    #Tflag = False'''


if __name__ == '__main__':
    global emotion
    global run
    run = True
    #emotion = russell(mac_addr="20:68:9D:3F:4F:88",settingFile='setting.arduino.txt',useSettingFile=True)
    emotion = russell(settingFile='setting.arduino.txt',useSettingFile=True)
    signal.signal(signal.SIGINT, handler)
    #the following line should be run on threading
    print('Waiting')
    while run:
        if emotion.isUpdate():
            print(emotion.getScopePercent(),'BPM:',emotion.bpm())
        time.sleep(0.5)
