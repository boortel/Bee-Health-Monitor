import os
import csv
import time
import json
import queue
import logging
import datetime
import threading

#import paho.mqtt.client as mqtt

from numpy import NaN

# Import the sensors
from sensors.microphone import Microphone
from sensors.MeasurementsThread import MeasurementsThread, queueMeasurementAVG, eventMeasurements_run, eventMeasurementAVG_read

# Import the bee counters
from BeeCounter.BeeCounterThread import eventBeeCounterRead, queueBeeCounterRead

# Event to run the SensorsThread internal loop and to lock the measurement
eventSensorsThread_run = threading.Event()

# MQTT helper functions
def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code {}".format(rc))

def on_message():
    logging.info("Message sent to DB")

MQTT_EN = False
MQTT_PATH = "name_of_topic"
MQTT_SERVER = "address_of_server"

# Sensor handle thread
class SensorsThread(threading.Thread):
    def __init__(self, name, baseLog, config):
        super(SensorsThread, self).__init__()
        self.name = name
        
        # Get the ini values
        self.periodSensor = config.getint('Sensors', 'period_threadSensors')
        self.recordTime = config.getint('Sensors', 'recordTime')
        
        # Initialize and run the MeasurementsThread
        self.measurements_thread = MeasurementsThread()
        
        # Initialize the microphone and indication LED
        self.microphone = Microphone(self.recordTime, baseLog)
        
        # TODO add LED control
        
        # Open the log file and create header
        try:
            self.fileName = os.path.join(baseLog, 'SensorLog.csv')

            # Open the csv and write header
            row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 'TempIn (°C)', 'HumIn (%)', 'TempOut (°C)', 'HumOut (%)', 'Pressure (hPa)', 'Light (lux)', 'BeeIn (-)', 'BeeOut (-)']
            with open(self.fileName, 'w', newline = '') as csvFile:
                writer = csv.writer(csvFile, delimiter =';')
                writer.writerow(row)
        except:
            logging.error(': Initialization of the log file failed.')
            
        # Initialize MQTT
        if MQTT_EN:
            self.client = mqtt.Client()
            self.client.on_connect = on_connect

            # Enable TLS for secure connection
            self.client.tls_set()
            self.client.username_pw_set("username", "password")
            
            #Connect to MQTT broker
            try:
                self.client.connect(MQTT_SERVER, 8883)
            except:
                logging.error(": Could not connect to client")
                
            self.client.loop_start()
            self.last_message = ""

        eventSensorsThread_run.set()

    def stop(self):
        # Stop the Measurements thread
        eventMeasurements_run.clear()
        eventMeasurementAVG_read.clear()
        
        # Empty the queue
        while not queueMeasurementAVG.empty():
            queueMeasurementAVG.get()
        
        # TODO add LED control
        #self.LED.off()
        
        if MQTT_EN:
            self.client.loop_stop()

    def run(self):
        
        self.measurements_thread.start()
        
        # This loop is run until stopped from main
        while eventSensorsThread_run.is_set():

            # Get the start time
            measurement_period_start = time.time()
            
            # TODO add LED control
            #self.LED.on()
            
            # Wait for measurement according the set time
            measurement_period_actual = time.time()
            measurement_period = measurement_period_actual - measurement_period_start
            
            while (measurement_period < (self.periodSensor - self.recordTime)) and eventMeasurements_run.is_set():
                time.sleep(0.1)
                measurement_period_actual = time.time()
                measurement_period = measurement_period_actual - measurement_period_start
                
            if not eventMeasurements_run.is_set():
                logging.info(": Measurement stopped, exiting the sensor thread")
                break
                
            # TODO add LED control
            #self.LED.toggle()
            
            # Get the timestamp
            now = datetime.datetime.now()
            timeStampM = now.strftime("%Y.%m.%d %H:%M:%S")

            # Get average values from sensors
            try:        
                eventMeasurementAVG_read.set()
                co2_eq_ppm, tvoc_ppb, TempIn, HumIn, TempOut, HumOut, PressOut, Light = queueMeasurementAVG.get(timeout = 15)
            except queue.Empty:
                logging.error(": Sensor reading timed out")
                
                co2_eq_ppm = NaN
                tvoc_ppb = NaN
                TempIn = NaN
                HumIn = NaN
                TempOut = NaN
                HumOut = NaN
                PressOut = NaN
                Light = NaN

            # Get values from the bee counters
            #try:
            #    eventBeeCounterRead.set()
            #    BeeIn, BeeOut = queueBeeCounterRead.get(timeout = 5)
            #except:
            #    BeeIn = NaN
            #    BeeOut = Nan
                
            BeeIn = 0
            BeeOut = 0
            
            # Log the new values through the set period
            row = [f'{timeStampM:s}', f'{co2_eq_ppm:.2f}', f'{tvoc_ppb:.2f}', f'{float(TempIn):.2f}', 
                   f'{float(HumIn):.2f}', f'{float(TempOut):.2f}', f'{float(HumOut):.2f}', f'{float(PressOut):.2f}',
                   f'{float(Light):.2f}', f'{BeeIn}', f'{BeeOut}']

            try:    
                with open(self.fileName, 'a', newline = '') as csvFile:
                    writer = csv.writer(csvFile, delimiter =';')
                    writer.writerow(row)
                logging.info(': Sensor data were written to the log.')
            except:
                logging.error(': Writing to log file failed.')
                
            if MQTT_EN:
                # Check if connected to broker, if not store the message and send it next time
                data = {
                    "timestamp": timeStampM,
                    "co2_eq_ppm": co2_eq_ppm,
                    "tvoc_ppb": tvoc_ppb,
                    "TempIn": TempIn,
                    "HumIn": HumIn,
                    "TempOut": TempOut,
                    "HumOut": HumOut,
                    "PressOut": PressOut,
                    "Light": Light,
                    "BeeIn": BeeIn,
                    "BeeOut": BeeOut
                }
                json_str = json.dumps(data)
                
                try:
                    if (self.client.is_connected()):
                        if len(self.last_message) > 0:
                            self.client.publish(MQTT_PATH, self.last_message)
                            logging.info(": Last message sent to DB")
                            self.last_message = ""
                        self.client.publish(MQTT_PATH, json_str)
                        logging.info(": Message sent to DB") 
                    else:
                        self.client.connect(MQTT_SERVER, 8883)
                        self.client.publish(MQTT_PATH,json_str)
                except:
                    self.last_message = json_str
                    logging.info(": Could not send message to DB")

            # Record the sound
            self.microphone.record()
            
            # TODO add LED control
            #self.LED.on()

            # Measure the overall processing time
            measurement_period_stop = time.time()
            measurement_period = measurement_period_stop - measurement_period_start
                