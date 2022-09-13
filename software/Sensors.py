import time
import logging

from numpy import NaN

# Import Grove stuff
import seeed_dht
import seeed_sgp30
from grove.i2c import Bus
from grove.factory import Factory
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from TempPress import piqmp6988SM as QMP6988
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
            # Initialize the value arrays
            HumIn = [0]*5
            TempIn = [0]*5

            # Get 5 values for a floating average computation
            for i in range(5):
                HumIn[i], TempIn[i] = self.DHT11.read()
                self.errorMeasure = 0
                time.sleep(1)
        except:
            if self.errorMeasure == 0:
                logging.error(': DHT11 sensor ', str(self.order), ' communication (one-wire) failure.')
                self.errorMeasure = 1

            HumIn = NaN
            TempIn = NaN

        HumIn = sum(HumIn)/5
        TempIn = sum(TempIn)/5

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
            # Initialize the value arrays
            co2_eq_ppm = [0]*5
            tvoc_ppb = [0]*5

            # Get 5 values for a floating average computation
            for i in range(5):
                gData = self.SGP30.read_measurements()
                co2_eq_ppm[i], tvoc_ppb[i] = gData.data

                self.errorMeasure = 0
                time.sleep(1)
        except:
            if self.errorMeasure == 0:
                logging.error(': Gass sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasure = 1
            
            co2_eq_ppm = NaN
            tvoc_ppb = NaN

        co2_eq_ppm = sum(co2_eq_ppm)/5
        tvoc_ppb = sum(tvoc_ppb)/5

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
            # Initialize the value arrays
            TempOut = [0]*5
            HumOut = [0]*5

            # Get 5 values for a floating average computation
            for i in range(5):
                TempOut[i], HumOut[i] = self.SHT31.read()
                self.errorMeasureSHT = 0
                time.sleep(1)
        except:
            if self.errorMeasureSHT == 0:
                logging.error(': Atmosphere sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasureSHT = 1
            
            TempOut = NaN
            HumOut = NaN

        TempOut = sum(TempOut)/5
        HumOut = sum(HumOut)/5

        try:
            # Initialize the value arrays
            PressOut = [0]*5

            # Get 5 values for a floating average computation
            for i in range(5):
                values = self.qmp.read()
                PressOut[i] = values['pressure']

                self.errorMeasureQMP = 0
                time.sleep(1)
        except:
            if self.errorMeasureQMP == 0:
                logging.error(': Pressure sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasureQMP = 1

            PressOut = NaN

        PressOut = sum(PressOut)/5

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
            # Initialize the value arrays
            lightOut = [0]*5

            # Get 5 values for a floating average computation
            for i in range(5):
                lightOut[i] = self.daylg.light
                self.errorMeasure = 0
                time.sleep(1)
        except:
            if self.errorMeasure == 0:
                logging.error(': Light sensor ', str(self.order), ', or hat communication (I2C) failure.')
                self.errorMeasure = 1
            
            lightOut = NaN

        lightOut = sum(lightOut)/5

        return lightOut

class Relay(object):
    # Class to control relay
    def __init__(self, order, port):
        self.state = 0

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
            self.state = 1
            self.errorOn = 0
        except:
            if self.errorOn == 0:
                logging.error(': Relay ', str(self.order), ' failure.')
                self.errorOn = 1

    def off(self):
        try:
            self.relay.off()
            self.state = 0
            self.erroOff = 0
        except:
            if self.erroOff == 0:
                logging.error(': Relay ', str(self.order), ' failure.')
                self.erroOff = 1

    def toggle(self):
        if self.state == 0:
            self.on()
        else:
            self.off()