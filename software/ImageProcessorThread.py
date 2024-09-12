
import configparser
import threading
import datetime
import logging
import cv2
import os
import io

import numpy as np

from PIL import Image

from BeeCounter.BeeCounterThread import queueBeeCounter
from BeeCounter.background import BackgroundModel

# Image processing thread
class ImageProcessor(threading.Thread):
    def __init__(self, owner, camPath, ROI, log_dec, background_init_frame, color):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.owner = owner

        print("Vnutri konstruktora ImageProcessor")
        self.camPath = camPath
        self.ROI = ROI
        self.log_dec = log_dec

        self.counter = 0

        self.color = color
        WhiteT = (50, 50, 30, 5000)
        IRT = (50, 50, 30, 5000)
        TurT = (50, 50, 30, 5000)#turtle :-D
        BackgroundFeatures=(WhiteT, IRT, TurT)


        self.colors = ["W","IR","Tur"]
        #create folders for images
        for i in self.colors:
            if not os.path.exists(self.camPath + '/' + i):
                os.makedirs(self.camPath + '/' + i)
        # Initialize the dynamic background model
        if background_init_frame is not None:
            #background_init_frame = background_init_frame[20:, bins[0]:bins[1], ...]
            background_init_frame = cv2.cvtColor(background_init_frame, cv2.COLOR_BGR2GRAY)
        #self.models=list()


        #self.dyn_model = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frame)
        try:
            self.dyn_model = BackgroundModel(BackgroundFeatures[color], background_init_frame=background_init_frame)#zatial robi problemy toto
        except:
            print("Background model robi patalie")
        #self.models[0] = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frameW)
        #self.models[1] = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frameIR)
        #self.models[2] = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frameTur)

        self.start()

    def run(self):
        # This method runs in a separate thread
        #print("ImageProcessor thread bezi")
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)

                    # Read the image and do some processing on it
                    image = Image.open(self.stream)
                    image = image.crop(self.ROI)

                    # RGB -> BGR, Color to Gray
                    image_bgr = np.asarray(image)[..., ::-1]
                    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
                    
                    print("pred zistovanim update")#sem to skace
                    # Process only dynamic images
                    if self.dyn_model.update(gray):
                        # Put the image to the BeeCounter queue
                        queueBeeCounter.put(image_bgr)

                        # Iterate the logging counter
                        self.counter += 1

                        print("bol updatnuty obrazok, som tesne pred ukladanim")
                        # Log the image
                        if self.counter >= self.log_dec:#tu su patalie
                            try:
                                print("1")
                                now = datetime.datetime.now()
                                print("2")
                                imgLog = self.camPath + '/' + self.colors[self.color] + '/' + now.strftime("%y%m%d_%H%M%S%f") + '.jpeg'
                                #imgLog = self.camPath + '/' + "W" + '/' + now.strftime("%y%m%d_%H%M%S%f") + '.jpeg'
                                print("3")
                                image.save(imgLog, 'jpeg')
                                print("4")
                            except:
                                print("Nejde ulozit obrazok")
                            print("Bol ulozeny obrazcok..... A mozno spravny, dopln kontrolu")
                            #logging.debug(': Write image as: ' + imgLog + '.')
                            self.counter = 0

                    # Set done to True if you want the script to terminate
                    # at some point
                    #self.owner.done=True

                except:
                    logging.error(': Attemp to read image stream failed.')
                    
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the available pool
                    with self.owner.lock:
                        self.owner.pool.append(self)