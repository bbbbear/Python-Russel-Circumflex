import threading

class THREADRUN():
    run = True
    def start(self):
        self.run = True
    def stop(self):
        self.run = False
    def status(self):
        return self.run
    def __str__(self):
        return str(self.run)

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
            return None

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
            return None




class PULSEIBI():
    def __init__(self,size=30,HRV_threshold = 2500):
        if size < 10:
            print('Err, the size of PNNx must greather than 10. Set to default 30')
            size = 30
        self.__IBI_array = [0]*size
        self.__IBI_count = 0
        self.__IBI_tail = 0

        self.__HRV_thresholded_array = [0]*size
        self.__HRV_count = 0
        self.__HRV_tail = 0
        if HRV_threshold < 0:
            print('Err, the threshold of HRV must greather than 0. Set to default 2500')
            self.__HRV_thres = 2500
        else:
            self.__HRV_thres = HRV_threshold

        self.__size = size
        self.__lock = threading.Lock()

    def put(self,newIBI):
        self.__lock.acquire()
        if newIBI < 0:
            self.__lock.release()
            print('Err, the IBI must be positive value. Input discarded')
            return
        #PUT new IBI data into a Circular array

        self.__IBI_array[self.__IBI_tail] = newIBI
        #Count the IBI data
        if self.__IBI_count < self.__size:
            self.__IBI_count += 1

        #Thresholding the HRV
        if self.__IBI_count > 1:
            if (newIBI - self.__IBI_array[self.__IBI_tail - 1])**2 > 2500:
                self.__HRV_thresholded_array[self.__HRV_tail] = 1
            else:
                self.__HRV_thresholded_array[self.__HRV_tail] = 0

            if self.__HRV_count < self.__size:
                self.__HRV_count += 1

            self.__HRV_tail = (self.__HRV_tail + 1) % self.__size   #Next tail calculation
        self.__IBI_tail = (self.__IBI_tail + 1) % self.__size       #Next tail calculation
        self.__lock.release()

    def getHRVthresholded(self):
        self.__lock.acquire()
        if self.__IBI_count != self.__size:
            self.__lock.release()
            print 'Err, the IBI data has only',self.__IBI_count, 'of', self.__size, '[Return None]'
            return None
        else:
            ret = float(sum(self.__HRV_thresholded_array))/self.__size
            self.__lock.release()
            return ret

    def getAll(self):
        self.__lock.acquire()
        ret = self.__IBI_array[self.__IBI_tail:] + self.__IBI_array[:self.__IBI_tail]
        self.__lock.release()
        return ret

    def getBPM(self,n=10):
        self.__lock.acquire()
        if self.__IBI_count < n:
            self.__lock.release()
            print 'Err, the IBI data has only',self.__IBI_count, 'of',n, '[Return None]'
            return None
        if self.__IBI_count < self.__size:
            ret = self.__findBPM(self.__IBI_array[self.__IBI_tail-n:self.__IBI_tail])
        elif (self.__size - self.__IBI_tail) >= n:
            ret = self.__findBPM(self.__IBI_array[self.__IBI_tail:self.__IBI_tail+n])
        else:
            overlap = self.__IBI_tail - self.__size + n
            ret = self.__findBPM(self.__IBI_array[self.__IBI_tail:]+self.__IBI_array[:overlap])
        self.__lock.release()
        return ret

    def __findBPM(self,data):
        return 60000.0/(sum(data)/len(data))


    def reset(self):
        self.__lock.acquire()
        self.__IBI_array = [0]*self.__size
        self.__IBI_count = 0
        self.__IBI_tail = 0

        self.__HRV_thresholded_array = [0]*self.__size
        self.__HRV_count = 0
        self.__HRV_tail = 0
        self.__lock.release()
