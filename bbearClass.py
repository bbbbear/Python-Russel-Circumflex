import threading
import numpy as np

class BOOL():
    def __init__(self,value=True):
        self.__bool = value
    def true(self):
        self.__bool = True
    def false(self):
        self.__bool = False
    def get(self):
        return self.__bool
    def __str__(self):
        return str(self.__bool)
    def __nonzero__(self):
        return self.__bool

#No lock, the queue is already locked by caller
class QUEUE():
    def __init__(self,maxsize = 100):
        if maxsize < 1:
            print('Err, max-size of queue must greather than 1')
        self.__size = maxsize
        self.__item = []
        self.__len = 0
        #self.__lock = threading.Lock()

    def put(self,item):
        #self.__lock.acquire()
        if self.__len < self.__size:
            self.__item.append(item)
            self.__len += 1
        else:
            print('Queue is full, input discarded')
        #self.__lock.release()

    def get(self):
        #self.__lock.acquire()
        if self.__len > 0:
            self.__len -= 1
            ret = self.__item.pop(0)
            #self.__lock.release()
            return ret
        else:
            #self.__lock.release()
            print 'Err, No data'
            return []

    def getAll(self):
        #self.__lock.acquire()
        if self.__len > 0:
            ret = list(self.__item)
            self.__item = []
            self.__len = 0
            #self.__lock.release()
            return ret
        else:
            #self.__lock.release()
            print 'Err, No data'
            return []




class PULSEIBI():
    #Use the Circular array to make sure that the most recent data will always be used
    def __init__(self,size=30,pNNx = 50):
        if size < 10:
            print('Err, the size of PNNx must greather than 10. Set to minimum possible 10')
            size = 10
        self.__IBI_array = [0]*size
        self.__IBI_count = 0
        self.__IBI_tail = 0

        self.__pNNx_array = [0]*size
        self.__NN_count = 0
        self.__pNNx_tail = 0
        if pNNx < 0:
            print('Err, the threshold of HRV must greather than 0. Set to default 2500')
            self.__pNNx_thres = pNNx**2
        else:
            self.__pNNx_thres = pNNx**2

        self.__size = size
        self.__lock = threading.Lock()

    def put(self,newIBI):
        with self.__lock:
            #self.__lock.acquire()
            if newIBI < 0:
            #    self.__lock.release()
                print('Err, the IBI must be positive value. Input discarded')
                return
            #PUT new IBI data into a Circular array

            self.__IBI_array[self.__IBI_tail] = newIBI
            #Count the IBI data
            if self.__IBI_count < self.__size:
                self.__IBI_count += 1

            #Thresholding the HRV for pNN50
            if self.__IBI_count > 1:
                #Check if consecutive NN intervals that differ by more than 50 ms
                if (newIBI - self.__IBI_array[self.__IBI_tail - 1])**2 > self.__pNNx_thres:
                    self.__pNNx_array[self.__pNNx_tail] = 1
                else:
                    self.__pNNx_array[self.__pNNx_tail] = 0

                if self.__NN_count < self.__size:
                    self.__NN_count += 1

                self.__pNNx_tail = (self.__pNNx_tail + 1) % self.__size   #Next tail calculation
            self.__IBI_tail = (self.__IBI_tail + 1) % self.__size       #Next tail calculation
            #self.__lock.release()

    def pNNx(self):
        with self.__lock:
            #self.__lock.acquire()
            if self.__IBI_count < 10:
            #    self.__lock.release()
                print 'Err, the IBI data has only',self.__IBI_count, 'of', 10, '[Return None]'
                return None
            else:
                data = self.__pNNx_array[:self.__NN_count]
                size = self.__NN_count
            #else:
            #    ret = float(sum(self.__pNNx_array))/self.__size
        #        self.__lock.release()
        return float(sum(data))/size

    def getAll(self):
        with self.__lock:
            #self.__lock.acquire()
            first = self.__IBI_array[self.__IBI_tail:]
            second = self.__IBI_array[:self.__IBI_tail]
            #self.__lock.release()
        return first+second

    def BPM(self,n=10):
        #self.__lock.acquire()
        with self.__lock:
            if self.__IBI_count < 10:
            #    self.__lock.release()
                print 'Err, the IBI data has only',self.__IBI_count, 'of',10, '[Return None]'
                return None
            #More than 10
            if self.__IBI_count < self.__size:
                ret = self.__findBPM(self.__IBI_array[self.__IBI_tail-n:self.__IBI_tail])
            elif (self.__size - self.__IBI_tail) >= n:
                ret = self.__findBPM(self.__IBI_array[self.__IBI_tail:self.__IBI_tail+n])
            else:
                overlap = self.__IBI_tail - self.__size + n
                ret = self.__findBPM(self.__IBI_array[self.__IBI_tail:]+self.__IBI_array[:overlap])
        #    self.__lock.release()
            return ret

    def __findBPM(self,data):
        return 60000.0/(sum(data)/len(data))


    def reset(self):
        with self.__lock:
            #self.__lock.acquire()
            self.__IBI_array = [0]*self.__size
            self.__IBI_count = 0
            self.__IBI_tail = 0

            self.__pNNx_array = [0]*self.__size
            self.__NN_count = 0
            self.__pNNx_tail = 0
            #self.__lock.release()

class CIR_ARRAY():
    def __init__(self,size):
        self.__data = []
        self.__index = 0
        self.__count = 0
        self.__size = size

    def put(self, obj):
        if self.__count < self.__size:
            self.__data.append(list(obj))
            self.__count += 1
        else:
            self.__data[self.__index] = list(obj)
        self.__index = (self.__index + 1) % self.__size


    def get(self,order=False):
        if self.__count < self.__size:
            return self.__data[:self.__index]
        else:
            if order:
                return self.__data[self.__index:] + self.__data[:self.__index]
            else:
                return self.__data

    def reset(self):
        self.__init__(self.__size)

#change to CIR_ARRAY
class RAWPULSE():
    def __init__(self,length=3,diff = -0.002):
        self.__size = int(length*abs(1/diff))+1
        self.__pulseData = [0]*self.__size
        self.__pulseLabel = np.round(np.arange(0.000,-length+diff,diff),3).tolist()
        self.__limit = -length-0.002
        self.__lock = threading.Lock()
        self.__head = self.__size

    def put(self,data):
        with self.__lock:
            self.__head = (self.__head - 1)%self.__size
            self.__pulseData[self.__head] = data

    def label(self):
        with self.__lock:
            return self.__pulseLabel

    def get(self):
        with self.__lock:
            first = self.__pulseData[self.__head:]
            second = self.__pulseData[:self.__head]
        return first+second

    def reset(self):
        with self.__lock:
            self.__pulseData[:] = 0
            self.__head = self.__size

    def size(self):
        return self.__size
