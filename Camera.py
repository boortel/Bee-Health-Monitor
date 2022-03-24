import datetime
import logging
import time
import os

from picamera import PiCamera

# Import and define globals
captureStatus = True

def setCaptureStatus(status):
    global captureStatus
    captureStatus = status

class Camera:
    # Class to control rPi HQ camera
    def __init__(self, fps, exp, iso, ROI, logPath):
        self.errorCapture = 0

        # Camera log base path
        self.camPath = logPath + '/CameraLog'
        if not os.path.exists(self.camPath):
            os.makedirs(self.camPath)

        try:
            # Open the camera reference, set the iso and wait to settle
            self.camera = PiCamera(resolution=(1280, 720), framerate=fps)
            self.camera.iso = iso
            time.sleep(2)

            # Set the shutter speed and disable automatic setting
            self.camera.shutter_speed = exp
            self.camera.exposure_mode = 'off'

            # Fix the white balance
            g = self.camera.awb_gains
            self.camera.awb_mode = 'off'
            self.camera.awb_gains = g

            # Set the ROI
            x, y, w, h = ROI
            self.camera._set_zoom([x, y, w, h])
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': rPi HQ camera initialization failure.')

    def __del__(self):
        try:
            self.camera.close()
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': rPi HQ camera closing failure.')

    def capture(self):
        global captureStatus

        try:
            # Capture sequence until the stop flag occurs
            for filename in self.camera.capture_continuous(self.camPath + '/{timestamp:%y%m%d_%H%M%S}-{counter:03d}.jpg'):
                if captureStatus == False:
                    break
                
            self.errorCapture = 0
            
        except:
            if self.errorCapture == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Camera capturing failure... ')
                self.errorCapture = 1
