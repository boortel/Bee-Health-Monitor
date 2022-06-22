import logging
import threading
import queue
import time
import numpy as np

BUFF_SIZE = 10
queueBeeCounter = queue.Queue(BUFF_SIZE)
eventBeeCounter = threading.Event()
eventBeeCounter.set()

class BeeCounterThread(threading.Thread):
    def __init__(self, processor_class, processor_args, name):
        super().__init__()
        self.processors = [processor_class(arg) for arg in processor_args]
        self.counters = [processor.bee_counter for processor in self.processors]
        self.name = name

    def run(self):
        while eventBeeCounter.is_set():
            if queueBeeCounter.empty():
                time.sleep(0.01)
                continue
            img = queueBeeCounter.get()
            logging.debug(f'Getting img : {str(queueBeeCounter.qsize())} items in queue')
            # RGB -> BGR
            img = np.asarray(img)[..., ::-1]
            for processor in self.processors:
                processor.update(img)
