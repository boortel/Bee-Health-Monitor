import datetime
import logging
import time

from picamera import PiCamera

class Camera:
    # Class to control rPi HQ camera
    def __init__(self, fps, exp, ROI):
        try:
            self.camera = PiCamera(resolution=(1280, 720), framerate=fps)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': rPi HQ camera initialization failure.')

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