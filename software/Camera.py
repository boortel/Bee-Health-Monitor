import configparser
import threading
import datetime
import logging
import json
import time
import os

from functools import partial
from picamera import PiCamera
from ImageProcessorThread import ImageProcessor

from BeeCounter.tracker import Tunnel
from BeeCounter.BeeCounterThread import BeeCounterThread, eventBeeCounter

# Global variable to pause camera capturing
captureStatus = True

# Function to set the capture pause control variable
def setCaptureStatus(status):
    global captureStatus
    captureStatus = status

# Object to create image processing and saving threads
class ProcessOutput(object):
    def __init__(self, camPath, ROI):
        self.done = False
        # Construct a pool of 4 image processors along with a lock
        # to control access between threads
        self.lock = threading.Lock()
        self.pool = [ImageProcessor(self, camPath, ROI) for i in range(4)]
        self.processor = None
        self.busy = False

        # Prepare the bee counter code
        logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-5s) %(message)s')

        base_path = os.path.dirname(os.path.realpath(__file__))

        # Get and parse the configuration file 
        cfg_path = os.path.join(base_path, 'BeeCounter/bee_counter.ini')
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        sections = cfg.getint('ImageProcessing', 'sections')
        arrived_threshold = cfg.getfloat('ImageProcessing', 'arrived_threshold')
        left_threshold = cfg.getfloat('ImageProcessing', 'left_threshold')
        track_max_age = cfg.getint('ImageProcessing', 'track_max_age')
        background_init_from_file = cfg.getboolean('ImageProcessing', 'background_init_from_file')

        # Get the initial background from file
        if background_init_from_file:
            background_init_frame = cv2.imread(os.path.join(base_path, 'data', 'background.jpg'))
        
        # Initialize the tunnels
        tunnel_func = partial(Tunnel, sections=sections, track_max_age=track_max_age, arrived_threshold=arrived_threshold, left_threshold=left_threshold, background_init_frame=background_init_frame)
        tunnel_args = json.loads(cfg.get('ImageProcessing', 'bins'))

        # Run the beeCounter thread
        beeCounter = BeeCounterThread(tunnel_func, tunnel_args, 'BeeCounterThread')
        beeCounter.start()

    def __del__(self):
        eventBeeCounter.clear()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame; set the current processor going and grab
            # a spare one
            if self.processor:
                self.processor.event.set()
            with self.lock:
                if self.pool:
                    self.processor = self.pool.pop()
                    self.busy = False
                else:
                    # No processor's available, we'll have to skip
                    # this frame; you may want to print a warning
                    # here to see whether you hit this case
                    self.processor = None

                    if self.busy == False:
                        logging.warning(': No processor available, the frame was skipeed.')
                        self.busy = True
                    
        if self.processor:
            self.processor.stream.write(buf)

    def flush(self):
        # When told to flush (this indicates end of recording), shut
        # down in an orderly fashion. First, add the current processor
        # back to the pool
        if self.processor:
            with self.lock:
                self.pool.append(self.processor)
                self.processor = None
        # Now, empty the pool, joining each thread as we go
        terminate = False

        while not terminate:
            with self.lock:
                try:
                    proc = self.pool.pop()
                except IndexError:
                    terminate = True
                    pass # pool is empty
            proc.terminated = True
            proc.join()

class Camera(object):
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
            self.camera.exposure_mode = 'off'
            self.camera.shutter_speed = 1 * exp

            # Fix the white balance
            g = self.camera.awb_gains
            self.camera.awb_mode = 'off'
            self.camera.awb_gains = g

            # Set the ROI
            self.ROI = ROI
            
        except:
            logging.error(': rPi HQ camera initialization failure.')

    def __del__(self):
        try:
            self.camera.close()
        except:
            logging.error(': rPi HQ camera closing failure.')

    def capture(self):
        global captureStatus

        if captureStatus == True:

            # Stop the capturing if run by accident
            if self.camera.recording == True:
                self.camera.stop_recording()

            try:
                logging.info(': rPi HQ camera starts capturing.')

                # Set the ProcessOutput object
                self.output = ProcessOutput(self.camPath, self.ROI)

                # Capture sequence in 1s intervals until the stop flag occurs
                self.camera.start_recording(self.output, format='mjpeg')

                while captureStatus == True:
                    self.camera.wait_recording(1)
                
                self.camera.stop_recording()

                logging.info(': rPi HQ camera stopped capturing.')
                    
                self.errorCapture = 0
                
            except:
                if self.errorCapture == 0:
                    logging.error(': Camera capturing failure... ')
                    self.errorCapture = 1