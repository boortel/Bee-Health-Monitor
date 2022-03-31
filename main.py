import configparser
import datetime
import logging
import time
import os

from SensorThread import SensorThread
from CameraThread import CameraThread

from Sensors import Relay

from Camera import setCaptureStatus
from CameraThread import setCamLogStatus
from SensorThread import setSensLogStatus

def main():
    # Initialize program logging
    logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-6s) %(message)s',)

    # Open the ini file
    cfg = configparser.ConfigParser()
    cfg.read('BeeLogger.ini')

    # Set the camera capture on and off times
    t_on = datetime.time(hour=6, minute=30)
    t_off = datetime.time(hour=18, minute=30)

    # Initialize the relay object
    relay = Relay(1, 5)

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

    # Run the threads
    sen.start()
    cam.start()

    log = True

    # Control the threads run and the camera capturing
    while log:
        t = datetime.time()

        # Turn on and off the camera capture together with the light
        if t >= t_on and t < t_off:
            setCaptureStatus(True)
            relay.on()
        else:
            setCaptureStatus(False)
            relay.off()

        # Optional: terminate the sensor and camera threads logging together with the program
        # Set custom condition
        #setCamLogStatus(False)
        #setSensLogStatus(False)
        #log = False

        time.sleep(0.1)


# Run the main function
if __name__ == '__main__':
    main()