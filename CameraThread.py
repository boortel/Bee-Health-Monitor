import threading
import datetime
import logging
import time

# Import the sensors
from Camera import Camera

# Global variable to stop camera capturing
camLogStatus = True

# Function to set the capture stop control variable
def setCamLogStatus(status):
    global camLogStatus
    camLogStatus = status


# Camera handle thread
class CameraThread(threading.Thread):
    def __init__(self, name, baseLog, config):
        super(CameraThread,self).__init__()
        self.name = name

        # Load the cfg from the ini-file
        fps = config.getint('Camera', 'fps')
        exp = config.getint('Camera', 'exp')
        iso = config.getint('Camera', 'iso')
        ROI = [config.getfloat('Camera', 'x'), config.getfloat('Camera', 'y'), \
               config.getfloat('Camera', 'w'), config.getfloat('Camera', 'h')]

        self.camera = Camera(fps, exp, iso, ROI, baseLog)

    def run(self):
        # This loop is run until stopped from main
        while camLogStatus:
            # Call the capture method periodicaly
            self.camera.capture()

            # Sleep until the next check
            time.sleep(0.1)