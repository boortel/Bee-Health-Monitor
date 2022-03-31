import datetime
import logging

from numpy import NaN

# Import Grove stuff
# TODO: Doresit snimani tlaku
import seeed_dht
import seeed_sgp30
from grove.i2c import Bus
from grove.factory import Factory
from grove.grove_light_sensor_v1_2 import GroveLightSensor
import grove.grove_temperature_humidity_sensor_sht3x as seed_sht31

class DHT11(object):
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self,  order, port):
        self.errorMeasure = 0

        self.order = order
        try:
            self.DHT11 = seeed_dht.DHT("11", port)
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': DHT11 sensor ', self.order, ' initialization failure.')

    def measure(self):
        try:
            HumIn, TempIn = self.DHT11.read()
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': DHT11 sensor ', self.order, ' communication (one-wire) failure.')
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
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': Gass sensor ', self.order, ' initialization failure.')
    
    def measure(self):
        try:
            gData = self.SGP30.read_measurements()
            co2_eq_ppm, tvoc_ppb = gData.data
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Gass sensor ', self.order, ' communication (I2C) failure.')
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
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': Atmosphere sensor ', self.order, ' initialization failure.')

        try:  
            self.QMP69 = 0
            # TODO: Doresit snimani tlaku
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': Pressure sensor ', self.order, ' initialization failure.')
    
    def measure(self):
        try:
            TempOut, HumOut = self.SHT31.read()
            self.errorMeasureSHT = 0
        except:
            if self.errorMeasureSHT == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Atmosphere sensor ', self.order, ' communication (I2C) failure.')
                self.errorMeasureSHT = 1
            
            TempOut = NaN
            HumOut = NaN

        try:
            PressOut = 0
            # TODO: Doresit snimani tlaku
            self.errorMeasureQMP = 0
        except:
            if self.errorMeasureQMP == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Pressure sensor ', self.order, ' communication (I2C) failure.')
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
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': Atmosphere sensor ', self.order, ' initialization failure.')

    def measure(self):
        try:
            lightOut = self.daylg.light
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Light sensor ', self.order, ', or hat communication (I2C) failure.')
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
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            logging.error(timeStamp + ': Relay ', self.order, ' initialization failure.')
                

    def on(self):
        try:
            self.relay.on()
            self.errorOn = 0
        except:
            if self.errorOn == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Relay ', self.order, ' failure.')
                self.errorOn = 1

    def off(self):
        try:
            self.relay.off()
            self.erroOff = 0
        except:
            if self.erroOff == 0:
                now = datetime.datetime.now()
                timeStamp = now.strftime("%y%m%d_%H%M%S")
                logging.error(timeStamp + ': Relay ', self.order, ' failure.')
                self.erroOff = 1