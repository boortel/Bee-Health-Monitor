import datetime
import logging
import time

from picamera import PiCamera

class Camera:
    # Class to control rPi HQ camera
    def __init__(self, fps, exp, ROI):
        self.errorCapture = 0
        self.errorSaving = 0

        self.fps = fps

        try:
            self.camera = PiCamera(resolution=(1280, 720), framerate=fps)
            time.sleep(2)

            # Set the exposition mode
            #TODO: podivat se na parametry
            self.camera.shutter_speed = exp
            self.camera.exposure_mode = 'off'

            g = self.camera.awb_gains
            self.camera.awb_mode = 'off'
            self.camera.awb_gains = g

            # Set the ROI
            x, y, w, h = ROI
            self.camera._set_zoom([x, y, w, h])
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': rPi HQ camera initialization failure.')

    def __del__(self):
        try:
            self.camera.close()
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': rPi HQ camera closing failure.')

    def capture(self):
        # Capture 1s long sequence
        self.camera.capture_sequence(['{timestamp:%y%m%d_%H%M%S}-{counter:03d}.jpg' % i for i in range(self.fps)])