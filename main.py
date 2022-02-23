import threading
import queue
import time
import logging
import random
import sys
import os


read_file = 'Pokus.txt'
log1 = open('Pokus1.txt', "a+")

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

BUF_SIZE = 10
q = queue.Queue(BUF_SIZE)

class ProducerThread(threading.Thread):
    def __init__(self, name):
        super(ProducerThread,self).__init__()
        self.name = name

    def run(self):
        with open(read_file, 'r') as f:
            for line in f:
                stripped = line.strip('\n\r')
                value1,value2,value3,value4,value5 = stripped.split(',')
                float_value1 = float(value1)
                if not q.full():
                    q.put(float_value1)
                    logging.debug('Putting ' + str(float_value1) + ' : ' + str(q.qsize()) + ' items in queue')
                    time.sleep(random.random())
        return

class ConsumerThread(threading.Thread):
    def __init__(self, name):
        super(ConsumerThread,self).__init__()
        self.name = name
        return

    def run(self):
        while not q.empty():
            float_value1 = q.get()
            sqr_value1 = float_value1 * float_value1
            log1.write("The square of " + str(float_value1) + " is " + str(sqr_value1))
            logging.debug('Getting ' + str(float_value1) + ' : ' + str(q.qsize()) + ' items in queue')
            time.sleep(random.random())
        return

if __name__ == '__main__':

    p = ProducerThread(name='producer')
    c = ConsumerThread(name='consumer')

    p.start()
    time.sleep(2)
    c.start()
    time.sleep(2)