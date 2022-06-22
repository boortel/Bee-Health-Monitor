import threading
import queue
import time

# Import the SGP30 sensor
from Sensors import SGP30

# Global variable to stop sensor logging
SGP30Status = True

# Function to stop the SensorThread internal loop
def stopSGP30Thread():
    global SGP30Status
    SGP30Status = False

# Queue and its control event to send SGP30 data
BUFF = 1
queueSGP30 = queue.Queue(BUFF)
eventSGP30 = threading.Event()

# SGP30 sensor has to be run every 1s in background to ensure a correct online calibration 

# Sensor handle thread
class SGP30Thread(threading.Thread):
    def __init__(self):
        super(SGP30Thread,self).__init__()
        self.SGP30_1 = SGP30(1)

    def run(self):
        # This loop is run until stopped from SensorThread
        while SGP30Status:

            # Get the data from SGP30 and sleep 1s
            co2_eq_ppm, tvoc_ppb = self.SGP30_1.measure()
            print(co2_eq_ppm)
            print(tvoc_ppb)
            time.sleep(1)

            # Put the data to the queue
            if eventSGP30.is_set():
                queueSGP30.put([co2_eq_ppm, tvoc_ppb])
                eventSGP30.clear()
