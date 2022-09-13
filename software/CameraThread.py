import threading
import datetime
import logging
import time

# Import the sensors
from Camera import Camera

# Event to stop camera capturing
eventCameraThread_run = threading.Event()

# Global variable to stop camera capturing
camLogStatus = True

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

        log_dec = config.getint('Camera', 'log_dec')

        self.camera = Camera(fps, exp, iso, ROI, baseLog, log_dec)

        eventCameraThread_run.set()

    def run(self):
        # This loop is run until stopped from main
        while eventCameraThread_run.is_set():
            # Call the capture method periodicaly
            self.camera.capture()

            # Sleep until the next check
            time.sleep(0.1)