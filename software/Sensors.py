import datetime
import logging
import time

from numpy import NaN

# Import Grove stuff
# TODO: Doresit snimani tlaku
import seeed_dht
import seeed_sgp30
from grove.i2c import Bus
from grove.factory import Factory
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from ..TempPress.piqmp6988sm import piqmp6988 as QMP6988
import grove.grove_temperature_humidity_sensor_sht3x as seed_sht31

config = {
    'temperature' : QMP6988.Oversampling.X4.value,
    'pressure' :    QMP6988.Oversampling.X32.value,
    'filter' :      QMP6988.Filter.COEFFECT_32.value,
    'mode' :        QMP6988.Powermode.NORMAL.value
} 

class DHT11(object):
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self,  order, port):
        self.errorMeasure = 0

        self.order = order
        try:
            self.DHT11 = seeed_dht.DHT("11", port)
        except:
            logging.error(': DHT11 sensor ', str(self.order), ' initialization failure.')

    def measure(self):
        try:
            HumIn, TempIn = self.DHT11.read()
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                logging.error(': DHT11 sensor ', str(self.order), ' communication (one-wire) failure.')
                self.errorMeasure = 1

            HumIn = NaN
            TempIn = NaN

        return HumIn, TempIn

class SGP30(object):
    # Class to control SGP30 gass sensor
    def __init__(self, order):
        self.errorMeasure = 0

        self.order = order
        try:
            self.SGP30 = seeed_sgp30.grove_sgp30(bus=Bus(1))
        except:
            logging.error(': Gass sensor ', str(self.order), ' initialization failure.')
    
    def measure(self):
        try:
            gData = self.SGP30.read_measurements()
            co2_eq_ppm, tvoc_ppb = gData.data
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                logging.error(': Gass sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasure = 1
            
            co2_eq_ppm = NaN
            tvoc_ppb = NaN

        return co2_eq_ppm, tvoc_ppb

class SHT31(object):
    # Class to control SHT31 temperature and humidity sensor together with the QMP6988 temperature and pressure sensor
    def __init__(self, order):
        self.errorMeasureSHT = 0
        self.errorMeasureQMP = 0

        self.order = order
        try:
            self.SHT31 = seed_sht31.GroveTemperatureHumiditySensorSHT3x(bus=Bus(1))
        except:
            logging.error(': Atmosphere sensor ', str(self.order), ' initialization failure.')

        try:  
            self.qmp = QMP6988.PiQmp6988(config)
        except:
            logging.error(': Pressure sensor ', str(self.order), ' initialization failure.')
    
    def measure(self):
        try:
            TempOut, HumOut = self.SHT31.read()
            self.errorMeasureSHT = 0
        except:
            if self.errorMeasureSHT == 0:
                logging.error(': Atmosphere sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasureSHT = 1
            
            TempOut = NaN
            HumOut = NaN

        try:
            values = self.qmp.read()
            PressOut = values['pressure']

            self.errorMeasureQMP = 0
        except:
            if self.errorMeasureQMP == 0:
                logging.error(': Pressure sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasureQMP = 1

            PressOut = NaN

        return TempOut, HumOut, PressOut

class LightS(object):
    # Class to control daylight sensor
    def __init__(self, order, port):
        self.errorMeasure = 0

        self.order = order
        try:
            self.daylg = GroveLightSensor(port)
        except:
            logging.error(': Light sensor ', str(self.order), ' initialization failure.')

    def measure(self):
        try:
            lightOut = self.daylg.light
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                logging.error(': Light sensor ', str(self.order), ', or hat communication (I2C) failure.')
                self.errorMeasure = 1
            
            lightOut = NaN

        return lightOut

class Relay(object):
    # Class to control relay
    def __init__(self, order, port):
        self.errorOn = 0
        self.erroOff = 0

        self.order = order
        try:
            self.relay = Factory.getGpioWrapper("Relay", port)
        except:
            logging.error(': Relay ', str(self.order), ' initialization failure.')
                

    def on(self):
        try:
            self.relay.on()
            self.errorOn = 0
        except:
            if self.errorOn == 0:
                logging.error(': Relay ', str(self.order), ' failure.')
                self.errorOn = 1

    def off(self):
        try:
            self.relay.off()
            self.erroOff = 0
        except:
            if self.erroOff == 0:
                logging.error(': Relay ', str(self.order), ' failure.')
                self.erroOff = 1