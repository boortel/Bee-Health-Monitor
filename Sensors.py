import datetime
import logging

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