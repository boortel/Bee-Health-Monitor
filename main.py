import configparser
import threading
import datetime
import logging
import random
import queue
import time
import os

from Threads import SensorThread, CameraThread
from Camera import setCaptureStatus

# Initialize program logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-6s) %(message)s',)

# Open the ini file
cfg = configparser.ConfigParser()
cfg.read('BeeLogger.ini')

class ControlThread(threading.Thread):
    def __init__(self, name):
        super(ControlThread, self).__init__()
        self.name = name
        return

    def run(self):
        while not q_ctl.empty():
            float_value1 = q_ctl.get()

            logging.debug('Getting ' + str(float_value1) + ' : ' + str(q_ctl.qsize()) + ' items in queue')
            time.sleep(random.random())
        return

# Run the main function
if __name__ == '__main__':

    BUF_SIZE = 10
    q_ctl = queue.Queue(BUF_SIZE)

    # Create the log directory and its structure if it not exists yet
    now = datetime.datetime.now()
    timeString = now.strftime("%y%m%d_%H%M")

    # Log session base path
    logPath = 'log/Log_' + timeString
    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Create the sensor and camera thread
    sen = SensorThread(name = 'sensor', baseLog = logPath, config = cfg)
    cam = CameraThread(name = 'camera', baseLog = logPath, config = cfg)
    #ctl = ControlThread(name='consumer')

    sen.start()
    cam.start()
    time.sleep(2)
    setCaptureStatus(False)