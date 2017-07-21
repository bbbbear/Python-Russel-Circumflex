from __future__ import print_function

from MindwaveMobileRawReader import MindwaveMobileRawReader
import struct
import collections
import time

from MindwavePacketPayloadParser import MindwavePacketPayloadParser

class MindwaveDataPointReader:
    def __init__(self, address=None):
        self._mindwaveMobileRawReader = MindwaveMobileRawReader(address=address)
        self._dataPointQueue = collections.deque()

    def start(self):
        self._mindwaveMobileRawReader.connectToMindWaveMobile()

    def isConnected(self):
        return self._mindwaveMobileRawReader.isConnected()

    def close(self):
        self._mindwaveMobileRawReader.close()

    def macaddr(self):
        return self._mindwaveMobileRawReader.macaddr()

    def readNextDataPoint(self):
        #print('z',end='')
        if (not self._moreDataPointsInQueue()):
        #    print('y',end='')
            self._putNextDataPointsInQueue()
        #    print('y',end='')
        #print('z',end='')
        return self._getDataPointFromQueue()

    def _moreDataPointsInQueue(self):
        return len(self._dataPointQueue) > 0

    def _getDataPointFromQueue(self):
        return self._dataPointQueue.pop();

    def _putNextDataPointsInQueue(self):
        #print('x',end='')
        dataPoints = self._readDataPointsFromOnePacket()
        #print('x',end='')
        self._dataPointQueue.extend(dataPoints)
        #print('x',end='')

    def _readDataPointsFromOnePacket(self):
        #print('w',end='')
        self._goToStartOfNextPacket()
        #print('w v',end='')
        payloadBytes, checkSum = self._readOnePacket()
        #print(' v ',end='')
        if (not self._checkSumIsOk(payloadBytes, checkSum)):
            #print ("checksum of packet was not correct, discarding packet...")
            return self._readDataPointsFromOnePacket();
        else:
            dataPoints = self._readDataPointsFromPayload(payloadBytes)
        self._mindwaveMobileRawReader.clearAlreadyReadBuffer()
        return dataPoints;

    def _goToStartOfNextPacket(self):
        while(True):
            #print('.',end='')
            byte = self._mindwaveMobileRawReader.getByte()
            #print('TYPE: ',type(byte))
            #time.sleep(5)
            if (byte == MindwaveMobileRawReader.START_OF_PACKET_BYTE):  # need two of these bytes at the start..
            #    print('t',end='')
                byte = self._mindwaveMobileRawReader.getByte()
            #    print('t',end='')
                if (byte == MindwaveMobileRawReader.START_OF_PACKET_BYTE):
                    # now at the start of the packet..
                    return;

    def _readOnePacket(self):
            #print('q',end='')
            payloadLength = self._readPayloadLength();
            #print('qp',end='')
            payloadBytes, checkSum = self._readPacket(payloadLength);
            #print('p',end='')
            return payloadBytes, checkSum

    def _readPayloadLength(self):
        payloadLength = self._mindwaveMobileRawReader.getByte()
        return payloadLength

    def _readPacket(self, payloadLength):
        #print('o',end='')
        payloadBytes = self._mindwaveMobileRawReader.getBytes(payloadLength)
        #print('o m',end='')
        checkSum = self._mindwaveMobileRawReader.getByte()
        #print('m',end='')
        return payloadBytes, checkSum

    def _checkSumIsOk(self, payloadBytes, checkSum):
        sumOfPayload = sum(payloadBytes)
        lastEightBits = sumOfPayload % 256
        invertedLastEightBits = self._computeOnesComplement(lastEightBits) #1's complement!
        return invertedLastEightBits == checkSum;

    def _computeOnesComplement(self, lastEightBits):
        return ~lastEightBits + 256

    def _readDataPointsFromPayload(self, payloadBytes):
        payloadParser = MindwavePacketPayloadParser(payloadBytes)
        return payloadParser.parseDataPoints();
