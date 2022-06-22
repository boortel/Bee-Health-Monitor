import threading
import datetime
import logging
import time

# Import the sensors
from Camera import Camera
from Camera import setCaptureStatus

# Global variable to stop camera capturing
camLogStatus = True

# Function to stop the CameraThread internal loop
def stopCamThread(relay):
    global camLogStatus

    # Stop the capturing, turn off the illumination and wait for a while
    setCaptureStatus(False)
    relay.off()
    time.sleep(0.1)

    # Stop the CameraThread
    camLogStatus = False


# Camera handle thread
class CameraThread(threading.Thread):
    def __init__(self, name, baseLog, config):
        super(CameraThread,self).__init__()
        self.name = name

        # Load the cfg from the ini-file
        fps = config.getint('Camera', 'fps')
        exp = config.getint('Camera', 'exp')
        iso = config.getint('Camera', 'iso')
        ROI = (config.getfloat('Camera', 'left'), config.getfloat('Camera', 'top'), \
               config.getfloat('Camera', 'right'), config.getfloat('Camera', 'bottom'))

        self.camera = Camera(fps, exp, iso, ROI, baseLog)

    def run(self):
        # This loop is run until stopped from main
        while camLogStatus:
            # Call the capture method periodicaly
            self.camera.capture()

            # Sleep until the next check
            time.sleep(0.1)