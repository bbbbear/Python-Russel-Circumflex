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
        if size < 1:
            print('Err, max-size of queue must greather than 1')
        self.__size = maxsize
        self.__item = []
        self.__len = 0

    def put(self,item):
        if self.__len < maxsize:
            self.__item.append(item)
            self.__len += 1
        else:
            print('Queue is full, input discarded')

    def get(self):
        if self.__len > 0:
            self.__len -= 1
            return self.__item.pop(0)
        else:
            print 'Err, No data'
            return None

    def getAll(self):
        if self.__len > 0:
            ret = self.__item[:self.__len]
            self.__len = 0
            return ret
        else:
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


    def put(self,newIBI):
        if newIBI < 0:
            print('Err, the IBI must be positive value. Input discarded')
            return
        #PUT new IBI data into a Circular array
        self.__IBI_array[self.__IBI_tail] = newIBI
        #Count the IBI data
        if self.__IBI_count < self.__size:
            self.__IBI_count += 1

        #Thresholding the HRV
        if self.__IBI_count > 1:
            if (self.__IBI_array[self.__IBI_tail] - self.__IBI_array[self.__IBI_tail - 1])**2 > 2500:
                self.__HRV_thresholded_array[self.__HRV_tail] = 1
            else:
                self.__HRV_thresholded_array[self.__HRV_tail] = 0

            if self.__HRV_count < self.__size:
                self.__HRV_count += 1

            self.__HRV_tail = (self.__HRV_tail + 1) % self.__size   #Next tail calculation
        self.__IBI_tail = (self.__IBI_tail + 1) % self.__size       #Next tail calculation

    def getHRVthresholded(self):
        if self.__IBI_count != self.__size:
            print('Err, the IBI data is not enough')
            return None
        else:
            return sum(self.___HRV_thresholded_array)/self.__size

    def getAll(self):
        return self.__IBI_array[self.__IBI_tail:] + self.__IBI_array[:self.__IBI_tail]

    def getBPM(self,n=10):
        if self.__IBI_count < n:
            print 'Err, the IBI data has only',self.__IBI_count, '.Return None'
            return None
        if (self.__size - self.__IBI_tail) >= n:
            return self.__findBPM(self.__IBI_array[self.__tail:self.__tail+n])
        else:
            overlap = self.__IBI_tail - self.__size + n
            return self.__findBPM(self.__IBI_array[self.__IBI_tail:]+self.__IBI_array[:overlap])

    def __findBPM(self,data):
        return 60000.0/(sum(data)/len(data))


    def reset(self):
        self.__IBI_array = [0]*self.__size
        self.__IBI_count = 0
        self.__IBI_tail = 0

        self.__HRV_thresholded_array = [0]*self.__size
        self.__HRV_count = 0
        self.__HRV_tail = 0
