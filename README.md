bbbeear message: Sorry, I haven't give a good commit history. This project use the russell's circumflex model to determine your emotion.
The implementation is based on Raspberry Pi 3 with python2 code

----------------------------------------------------------

Some scripts to access the data streamed by the **Neurosky Mindwave Mobile** Headset over Bluetooth on Linux.

Requirements:
* [PyBluez](http://code.google.com/p/pybluez/), see their [documentation](http://code.google.com/p/pybluez/wiki/Documentation) for installation instructions :)
For Ubuntu, installation might work like this:
```
sudo apt-get install libbluetooth-dev python-bluetooth
```


If you want to install the library as a module, do:
```
python setup.py install
```
from the root folder of the repository.

Afterwards, you can use it within python like this, with the headset set in pairing mode (http://support.neurosky.com/kb/mindwave-mobile/how-do-i-put-the-mindwave-mobile-into-discovery-mode):

```python
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
mindwaveDataPointReader = MindwaveDataPointReader()
# connect to the mindwave mobile headset...
mindwaveDataPointReader.start()
# read one data point, data point types are specified in  MindwaveDataPoints.py'
dataPoint = mindwaveDataPointReader.readNextDataPoint()
print dataPoint
``` 
