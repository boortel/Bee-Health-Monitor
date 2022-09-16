import threading
import queue

# Import the SGP30 sensor
from Sensors import SGP30

# Global variable to stop sensor logging
SGP30Status = True

# Event to stop the SGP30Thread internal loop
eventSGP30_run = threading.Event()

# Queue and its control event to send SGP30 data
BUFF = 1
queueSGP30 = queue.Queue(BUFF)
eventSGP30_read = threading.Event()

# SGP30 sensor has to be run every 1s in background to ensure a correct online calibration 

# Sensor handle thread
class SGP30Thread(threading.Thread):
    def __init__(self):
        super(SGP30Thread,self).__init__()
        eventSGP30_run.set()
        self.SGP30_1 = SGP30(1)

    def run(self):
        # This loop is run until stopped from SensorThread
        while eventSGP30_run.is_set():

            # Get the data from SGP30
            co2_eq_ppm, tvoc_ppb = self.SGP30_1.measure()

            # Put the data to the queue
            if eventSGP30_read.is_set():
                queueSGP30.put([co2_eq_ppm, tvoc_ppb])
                eventSGP30_read.clear()
