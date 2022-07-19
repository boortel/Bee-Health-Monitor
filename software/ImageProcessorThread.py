import threading
import datetime
import logging
import io

from PIL import Image

from BeeCounter.BeeCounterThread import queueBeeCounter

# Image processing thread
class ImageProcessor(threading.Thread):
    def __init__(self, owner, camPath, ROI, log_dec):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.owner = owner

        self.camPath = camPath
        self.ROI = ROI
        self.log_dec = log_dec

        self.counter = 0

        self.start()

    def run(self):
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)

                    # Read the image and do some processing on it
                    image = Image.open(self.stream)
                    image = image.crop(self.ROI)
                    
                    # Put the image to the BeeCounter queue
                    queueBeeCounter.put(image)

                    # Iterate the logging counter
                    self.counter += 1

                    # Log the image
                    if self.counter >= self.log_dec:
                        now = datetime.datetime.now()
                        imgLog = self.camPath + '/' + now.strftime("%y%m%d_%H%M%S%f") + '.jpeg'

                        image.save(imgLog, 'jpeg')
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
