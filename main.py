import configparser
import threading
import datetime
import logging
import random
import queue
import time
import csv
import sys
import os

from numpy import NaN

# Import Grove stuff
# TODO: Doresit snimani tlaku
import seeed_dht
import seeed_sgp30
from grove.i2c import Bus
from grove.factory import Factory
from grove.grove_sound_sensor import GroveSoundSensor
from grove.grove_light_sensor_v1_2 import GroveLightSensor
import grove.grove_temperature_humidity_sensor_sht3x as seed_sht31

# Import camera stuff
from picamera import PiCamera

# Initialize program logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

# Open the ini file
config = configparser.ConfigParser()
config.read('BeeLogger.ini')

class DHT11:
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self,  order, port):
        self.order = order
        try:
            self.DHT11 = seeed_dht.DHT("11", port)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': DHT11 sensor ', self.order, ' initialization failure.')

    def measure(self):
        try:
            HumIn, TempIn = self.DHT11.read()
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': DHT11 sensor ', self.order, ' communication (one-wire) failure.')

            HumIn = NaN
            TempIn = NaN

        return HumIn, TempIn

class SGP30:
    # Class to control SGP30 gass sensor
    def __init__(self, order):
        self.order = order
        try:
            self.SGP30 = seeed_sgp30.grove_sgp30(bus=Bus(1))
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Gass sensor ', self.order, ' initialization failure.')
    
    def measure(self):
        try:
            gData = self.SGP30.read_measurements()
            co2_eq_ppm, tvoc_ppb = gData.data
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Gass sensor ', self.order, ' communication (I2C) failure.')

            co2_eq_ppm = NaN
            tvoc_ppb = NaN

        return co2_eq_ppm, tvoc_ppb

class SHT31:
    # Class to control SHT31 temperature and humidity sensor together with the QMP6988 temperature and pressure sensor
    def __init__(self, order):
        self.order = order
        try:
            self.SHT31 = seed_sht31.GroveTemperatureHumiditySensorSHT3x(bus=Bus(1))
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Atmosphere sensor ', self.order, ' initialization failure.')

        try:  
            self.QMP69 = 0
            # TODO: Doresit snimani tlaku
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Pressure sensor ', self.order, ' initialization failure.')
    
    def measure(self):
        try:
            TempOut, HumOut = self.SHT31.read()
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Atmosphere sensor ', self.order, ' communication (I2C) failure.')
            TempOut = NaN
            HumOut = NaN

        try:
            PressOut = 0
            # TODO: Doresit snimani tlaku
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Pressure sensor ', self.order, ' communication (I2C) failure.')
            PressOut = NaN

        return TempOut, HumOut, PressOut

class LightS:
    # Class to control daylight sensor
    def __init__(self, order, port):
        self.order = order
        try:
            self.daylg = GroveLightSensor(port)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Atmosphere sensor ', self.order, ' initialization failure.')

    def measure(self):
        try:
            lightOut = self.daylg.light
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Light sensor ', self.order, ', or hat communication (I2C) failure.')
            lightOut = NaN

        return lightOut

class Relay:
    # Class to control relay
    def __init__(self, order, port):
        self.order = order
        try:
            self.relay = Factory.getGpioWrapper("Relay", port)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Relay ', self.order, ' initialization failure.')

    def on(self):
        try:
            self.relay.on()
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Relay ', self.order, ' failure.')

    def off(self):
        try:
            self.relay.off()
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Relay ', self.order, ' failure.')


class SensorThread(threading.Thread):
    def __init__(self, name):
        super(SensorThread,self).__init__()
        self.name = name

        self.period = config.getint('Sensors', 'period_thread')

        # Initialize the sensors objects
        self.DHT11_1 = DHT11(1, config.getint('Sensors', 'port_DHT11_1'))
        self.DHT11_2 = DHT11(2, config.getint('Sensors', 'port_DHT11_2'))
        self.SGP30_1 = SGP30(1)
        self.SHT31_1 = SHT31(1)
        self.Light_1 = LightS(1, config.getint('Sensors', 'port_LightS_1'))

        # Open the log file and create header
        try:
            datetime.datetime.now()
            now = datetime.datetime.now()
            timeString = now.strftime("%y%m%d_%H%M")
            fileName = 'log/SensorLog_' + timeString + '.csv'

            with open(fileName, 'w') as f:
                # create the csv writer
                self.writer = csv.writer(f)

            row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 'TempIn_1 (°C)', 'HumIn_1 (%)', 'TempIn_2 (°C)', 'HumIn_2 (%)', 'TempOut (°C)', 'HumOut (%)', 'Pressure (hPa)', 'Light (-)']
            self.writer.writerow(row)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Initialization of the log file failed.')

    def run(self):
        # Get the sensor data
        timeStamp = datetime.datetime.now()

        # SGP30 - gass sensor
        co2_eq_ppm, tvoc_ppb = self.SGP30_1.measure()

        # DHT11 - inner temperature and humidity
        HumIn_1, TempIn_1 = self.DHT11_1.measure()
        HumIn_2, TempIn_2 = self.DHT11_2.measure()

        # SHT31 - outer temperature, humidity and pressure
        TempOut, HumOut, PressOut = self.SHT31_1.measure()

        # Light sensor value
        Light = self.Light_1.measure()
        
        # Create log
        try:
            row = [timeStamp, co2_eq_ppm, tvoc_ppb, TempIn_1, HumIn_1, TempIn_2, HumIn_2, TempOut, HumOut, PressOut, Light]
            self.writer.writerow(row)

            logging.info(timeStamp, ': Sensor data were writen to the log.')
        except:
            logging.error(timeStamp, ': Writing to log file failed.')

        # Call the thread periodicaly
        threading.Timer(self.period, self.run).start()


class MicrophoneThread(threading.Thread):
    def __init__(self, name):
        super(MicrophoneThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani portu z ini souboru
        self.microphone = GroveSoundSensor(2)

    def run(self):
        sound = self.microphone.sound


class CameraThread(threading.Thread):
    def __init__(self, name):
        super(CameraThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani portu z ini souboru
        self.camera = PiCamera()

    def run(self):
        self.camera.start_preview()

    def stop(self):
        self.camera.stop_preview()


class ControlThread(threading.Thread):
    def __init__(self, name):
        super(ControlThread, self).__init__()
        self.name = name
        return

    def run(self):
        while not q_ctl.empty():
            float_value1 = q_ctl.get()

            logging.debug('Getting ' + str(float_value1) + ' : ' + str(q_ctl.qsize()) + ' items in queue')
            time.sleep(random.random())
        return


if __name__ == '__main__':

    BUF_SIZE = 10
    q_ctl = queue.Queue(BUF_SIZE)

    p = SensorThread(name='producer')
    c = ControlThread(name='consumer')

    p.start()
    time.sleep(2)
    c.start()
    time.sleep(2)