import logging
import threading
import queue
import time

BUFF_SIZE = 10
queueBeeCounterRead = queue.Queue(BUFF_SIZE)
queueBeeCounter = queue.Queue(BUFF_SIZE)

eventBeeCounterRead = threading.Event()
eventBeeCounter = threading.Event()

eventBeeCounterRead.clear()
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
            #logging.debug(f'Getting img : {str(queueBeeCounter.qsize())} items in queue')

            for processor in self.processors:
                processor.update(img)

            if eventBeeCounterRead.is_set():
                counterIn = 0
                counterOut = 0
                
                # Get the total number of bees in the single tunnels and restart the tunnel counters
                for counter in self.counters:
                    counterIn = counterIn + counter['up']
                    counter['up'] = 0

                    counterOut = counterOut + counter['down']
                    counter['down'] = 0
                
                # Put the data to the quee and free the BeeCounterRead event
                queueBeeCounterRead.put([counterIn, counterOut])
                eventBeeCounterRead.clear()
