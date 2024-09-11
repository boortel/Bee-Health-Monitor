import configparser
import threading
import datetime
import logging
import json
import time
import cv2
import os

from functools import partial
from picamera import PiCamera

from Sensors import Relay
from ImageProcessorThread import ImageProcessor

from BeeCounter.tracker import Tunnel
from BeeCounter.BeeCounterThread import BeeCounterThread, eventBeeCounter

# Event to stop camera capturing
eventCamera_capture = threading.Event()

# Object to create image processing and saving threads
class ProcessOutput(object):
    def __init__(self, camPath, ROI, log_dec, background_init_frame, SetColor):
    #def __init__(self, camPath, ROI, log_dec, background_init_frame):
        self.done = False
        print("Konstruktor ProcessOutput")
        # Construct a pool of 4 image processors along with a lock
        # to control access between threads        
        self.lock = threading.Lock()
        try:
            self.pool = [ImageProcessor(self, camPath, ROI, log_dec, background_init_frame, SetColor) for i in range(4)]
            #self.pool = [ImageProcessor(self, camPath, ROI, log_dec, background_init_frame) for i in range(4)]
        except:
            print("Pre zmenu odmieta vzniknut ImageProcessor")
        self.processor = None
        self.busy = False

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
    def __init__(self, fps, exp, iso, ROI, logPath, log_dec):
        self.errorCapture = 0
        self.i=0

        self.background_init_frames=list()

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

            # Set the ROI and logging decimation factor
            self.ROI = ROI
            self.log_dec = log_dec

            self.greenLED = Relay(2, 22)
            
        except:
            logging.error(': rPi HQ camera initialization failure.')

        try:
            # Prepare the bee counter code
            base_path = os.path.dirname(os.path.realpath(__file__))
            cfg_path = os.path.join(base_path, 'BeeCounter/bee_counter.ini')

            # Get and parse the configuration file 
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path)

            sections = cfg.getint('ImageProcessing', 'sections')
            arrived_threshold = cfg.getfloat('ImageProcessing', 'arrived_threshold')
            left_threshold = cfg.getfloat('ImageProcessing', 'left_threshold')
            track_max_age = cfg.getint('ImageProcessing', 'track_max_age')
            background_init_from_file = cfg.getboolean('ImageProcessing', 'background_init_from_file')

            # Get the initial background from file
            if background_init_from_file:
                self.background_init_frame=cv2.imread(os.path.join(base_path, 'BeeCounter/data/backgroundW.jpg'))
                self.background_init_frames.append(cv2.imread(os.path.join(base_path, 'BeeCounter/data/backgroundW.jpg')))
                self.background_init_frames.append(cv2.imread(os.path.join(base_path, 'BeeCounter/data/backgroundIR.jpg')))
                self.background_init_frames.append(cv2.imread(os.path.join(base_path, 'BeeCounter/data/backgroundTur.jpg')))
            else:
                self.background_init_frames.append(None)
                self.background_init_frames.append(None)
                self.background_init_frames.append(None)
            
            
            # Initialize the tunnels
            tunnel_func = partial(Tunnel, sections=sections, track_max_age=track_max_age, arrived_threshold=arrived_threshold, left_threshold=left_threshold, background_init_frame=self.background_init_frames[0])
            tunnel_args = json.loads(cfg.get('ImageProcessing', 'bins'))

            # Run the beeCounter thread
            self.beeCounter = BeeCounterThread(tunnel_func, tunnel_args, 'BeeCounterThread')
            self.beeCounter.start()

        except:
            logging.error(': BeeCounter thread initialization failure.')

    def __del__(self):
        try:
            self.camera.close()
        except:
            logging.error(': rPi HQ camera closing failure.')

        try:
            eventBeeCounter.clear()
            self.beeCounter.stop()
        except:
            logging.error(': BeeCounter thread closing failure.')

    def capture(self,SetColor):

        if eventCamera_capture.is_set():

            # Stop the capturing if run by accident
            if self.camera.recording == True:
                self.camera.stop_recording()

            try:
                logging.info(': rPi HQ camera starts capturing.')
                #logging.info(self.background_init_frames[0])
                # print(type(self.background_init_frames[0]))
                # print(self.background_init_frames[1])
                # print(self.background_init_frames[2])
                print("Pred ProcessOutput")#sem dojde
                # Set the ProcessOutput object
                try:
                    #self.output = ProcessOutput(self.camPath, self.ROI, self.log_dec, self.background_init_frame)
                    self.output = ProcessOutput(self.camPath, self.ROI, self.log_dec, self.background_init_frames[SetColor], SetColor)
                except:
                    print("ProcessOutput odmieta vzniknut")
               #self.output = ProcessOutput(self.camPath, self.ROI, self.log_dec, self.background_init_frame)
                print("Po ProcessOutput")
                print("Camera.py zacina s videom a posuva ho dalej")
                # Capture sequence in 1s intervals until the stop flag occurs
                self.camera.start_recording(self.output, format='mjpeg')
                while eventCamera_capture.is_set():
                    self.camera.wait_recording(1)
                    self.greenLED.toggle()
                    print("Video sa nataca z Camera.py")
                
                self.camera.stop_recording()
                self.greenLED.off()

                logging.info(': rPi HQ camera stopped capturing.')
                    
                self.errorCapture = 0
                
            except:
                if self.errorCapture == 0:
                    print("V Camera.py sa cosi pototo")
                    logging.error(': Camera capturing failure... ')
                    self.errorCapture = 1