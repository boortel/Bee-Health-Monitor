
import configparser
import threading
import datetime
import logging
import cv2
import os
import io

#import time

import numpy as np

from PIL import Image

from BeeCounter.BeeCounterThread import queueBeeCounter
from BeeCounter.background import BackgroundModel

GlobalColor=4

# Image processing thread
class ImageProcessor(threading.Thread):
    def __init__(self, owner, camPath, ROI, log_dec, color, base_path):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.owner = owner
        self.base_path=base_path

        print("Vnutri konstruktora ImageProcessor")
        self.camPath = camPath
        self.ROI = ROI
        self.log_dec = log_dec

        self.counter = 0

        self.color = color
        WhiteT = (50, 50, 30, 5000)#50
        IRT = (50, 50, 30, 5000)
        TurT = (50, 50, 30, 5000)#turtle :-D
        BackgroundFeatures=(WhiteT, IRT, TurT)
        try:
            self.background_init_frames=list()
            self.background_init_frames.append(cv2.imread(os.path.join(self.base_path, 'BeeCounter/data/backgroundW.jpg')))
            self.background_init_frames.append(cv2.imread(os.path.join(self.base_path, 'BeeCounter/data/backgroundIR.jpg')))
            self.background_init_frames.append(cv2.imread(os.path.join(self.base_path, 'BeeCounter/data/backgroundTur.jpg')))
            print("Pozadia nacital")
        except:
            print("Problem s nacitanim pozadi")



        try:
            self.colors = ["W","IR","Tur"]
            #create folders for images
            for i in self.colors:
                if not os.path.exists(self.camPath + '/' + i):
                    os.makedirs(self.camPath + '/' + i)
            # Initialize the dynamic background model
            for i in range(3):
                self.background_init_frames[i] = cv2.cvtColor(self.background_init_frames[i], cv2.COLOR_BGR2GRAY)
        except:
            print("Nevie spravit repozitare")


        #self.dyn_model = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frame)
        self.dyn_models=list()
        try:
            for i in range(3):
                self.dyn_models.append(BackgroundModel(BackgroundFeatures[i], background_init_frame=self.background_init_frames[i]))
        except:
            print("Background model robi patalie")

        self.start()

    def run(self):
        # This method runs in a separate thread
        #print("ImageProcessor thread bezi")
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    #start=time.time()
                    self.stream.seek(0)

                    # Read the image and do some processing on it
                    image = Image.open(self.stream)
                    image = image.crop(self.ROI)

                    # RGB -> BGR, Color to Gray
                    image_bgr = np.asarray(image)[..., ::-1]
                    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
                    
                    print("pred zistovanim update")#sem to skace
                    #print(GlobalColor)
                    # Process only dynamic images
                    try:
                        if self.dyn_models[GlobalColor].update(gray):# a sem to uz neskace, do macky
                            # Put the image to the BeeCounter queue
                            # queueBeeCounter.put(image_bgr)
                            # Iterate the logging counter
                            self.counter += 1

                            print("bol updatnuty obrazok, som tesne pred ukladanim")
                            # Log the image
                            if self.counter >= self.log_dec:
                                try:
                                    #print("1")
                                    now = datetime.datetime.now()
                                    #print("2")
                                    imgLog = self.camPath + '/' + self.colors[GlobalColor] + '/' + now.strftime("%y%m%d_%H%M%S%f") + '.jpeg'
                                    #print("3")
                                    image.save(imgLog, 'jpeg')
                                    #print("4")
                                except:
                                    print("Nejde ulozit obrazok")
                                print("Bol ulozeny obrazcok..... A mozno spravny, dopln kontrolu")
                                #logging.debug(': Write image as: ' + imgLog + '.')
                                self.counter = 0
                        # end=time.time()
                        # print(end-start)

                        # Set done to True if you want the script to terminate
                        # at some point
                        #self.owner.done=True
                    except:
                        print("Nieco sa pototo")

                except:
                    logging.error(': Attemp to read image stream failed.')
                    
                finally:
                    print("Do finale Image proc skace")
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the available pool
                    with self.owner.lock:
                        self.owner.pool.append(self)