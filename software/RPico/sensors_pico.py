import time
#import logging
import math
#from numpy import NaN
from utime import sleep_us


from machine import I2C, ADC, Pin
from dht11 import *
from dht20 import DHT20
import grove_sht31
import piqmp6988SM as QMP6988
from sgp30 import SGP30
from hx711 import HX711
from scales import Scales

config = {
    'temperature' : QMP6988.Oversampling.X4,
    'pressure' :    QMP6988.Oversampling.X32,
    'filter' :      QMP6988.Filter.COEFFECT_32,
    'mode' :        QMP6988.Powermode.NORMAL
} 


class DHT11(object):
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self,  order, port):
        self.errorMeasure = 0
        self.order = order

        try:
            self.DHT11 = DHT(port)
        except:
            print(': DHT11 sensor ', str(self.order), ' initialization failure.')

    def measure(self):
        try:
            # Initialize the value arrays
            HumIn = 0
            TempIn = 0

            # Get 5 values for a floating average computation

            TempIn, HumIn = self.DHT11.readTempHumid()
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                print(': DHT11 sensor ', str(self.order), ' communication (one-wire) failure.')
                self.errorMeasure = 1

            HumIn = math.nan
            TempIn = math.nan

        return HumIn, TempIn

class DHT21(object):
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self,  order):
        self.errorMeasure = 0
        self.order = order
        
        if order == 1:
            self.sda=Pin(8)
            self.scl=Pin(9)
            self.i2c=I2C(0,sda=self.sda, scl=self.scl, freq=400000)
        elif order == 2:
            self.sda=Pin(6)
            self.scl=Pin(7)
            self.i2c=I2C(1,sda=self.sda, scl=self.scl, freq=400000)
        else:
            print(': DHT20 sensor ', str(self.order), ' bad address.')
            
            
        try:
            self.DHT21 = DHT20(self.i2c)
        except:
            print(': DHT20 sensor ', str(self.order), ' initialization failure.')

    def measure(self):
        try:
            # Initialize the value arrays
            HumIn = 0
            TempIn = 0

            # Get 5 values for a floating average computation

            TempIn = self.DHT21.dht20_temperature()
            HumIn = self.DHT21.dht20_humidity()
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                print(': DHT20 sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasure = 1

            HumIn = math.nan
            TempIn = math.nan

        return HumIn, TempIn
    
class Sgp30(object):
    # Class to control SGP30 gass sensor
    def __init__(self, order):
        self.errorMeasure = 0
        self.order = order

        try:
            self.SGP30_1 = SGP30()
            self.SGP30_1.get_feature_set_version()
            self.SGP30_1.get_serial_id()
            self.SGP30_1.init_air_quality()
        except:
            print(': Gass sensor ', str(self.order), ' initialization failure.')
    
    def measure(self):
        try:
            # Initialize the value arrays
            co2_eq_ppm = 0
            tvoc_ppb = 0

            # Get 5 values for a floating average computation
            self.SGP30_1.measure_air_quality()
#             ♥gData = self.SGP30.read_measurements()
            co2_eq_ppm = self.SGP30_1.CO2eq
            tvoc_ppb = self.SGP30_1.TVOC

            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                print(': Gass sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasure = 1
            
            co2_eq_ppm = math.nan
            tvoc_ppb = math.nan

        return co2_eq_ppm, tvoc_ppb
    
class SHT31(object):
    # Class to control SHT31 temperature and humidity sensor together with the QMP6988 temperature and pressure sensor
    def __init__(self, order):
        self.errorMeasureSHT = 0
        self.errorMeasureQMP = 0

        self.order = order
        
        try:
            self.SHT31 = grove_sht31.GroveTemperatureHumiditySensorSHT3x()
        except:
            print(': Atmosphere sensor ', str(self.order), ' initialization failure.')

        try:
            self.qmp = QMP6988.PiQmp6988(config)
        except:
            print(': Pressure sensor ', str(self.order), ' initialization failure.')
    
    def measure(self):
        try:
            # Initialize the value arrays
            TempOut = 0
            HumOut = 0

            # Get 5 values for a floating average computation

            TempOut, HumOut = self.SHT31.read()
            self.errorMeasureSHT = 0

        except:
            if self.errorMeasureSHT == 0:
                print(': Atmosphere sensor ', str(self.order), ' communication (I2C) failure.')
                self.errorMeasureSHT = 1
            
            TempOut = math.nan
            HumOut = math.nan


        try:
            # Initialize the value arrays
            PressOut = 0

            # Get 5 values for a floating average computation
            values = self.qmp.read()
            PressOut = values['pressure']

            self.errorMeasureQMP = 0

        except:
            if self.errorMeasureQMP == 0:
#                 ♥logging.error(': Pressure sensor ', str(self.order), ' communication (I2C) failure.')
                print("")
                self.errorMeasureQMP = 1

            PressOut = math.nan

        return TempOut, HumOut, PressOut

class LightS(object):
    # Class to control daylight sensor
    def __init__(self, order, port):
        self.errorMeasure = 0
        self.order = order

        try:
            self.daylg = ADC(port)
        except:
            print(': Light sensor ', str(self.order), ' initialization failure.')

    def measure(self):
        try:
            # Initialize the value arrays
            lightOut = 0

            lightOut = self.daylg.read_u16()
            self.errorMeasure = 0
            time.sleep(0.1)
        except:
            if self.errorMeasure == 0:
                print(': Light sensor ', str(self.order), ', or hat communication (I2C) failure.')
                self.errorMeasure = 1
            
            lightOut = math.nan

        return lightOut
    
class hx_711(object):
    def __init__(self, order, d_out, pd_sck):
        self.order = order
        self.errorMeasure = 0
        try:
            self.scales = Scales(d_out, pd_sck)

        except:
            print(': HX711 sensor ', str(self.order), ' initialization failure.')
    
    def measure(self):
        #val = self.scales.stable_value()
        try:
            # Initialize the value arrays
            Weight = 0

            #if val := self.scales.raw_value():
            if val := self.scales.stable_value():
                Weight = val
            else:
                Weight = math.nan
                
            self.errorMeasure = 0
        except:
            if self.errorMeasure == 0:
                print(': HX711 sensor ', str(self.order), ' communication failure.')
                self.errorMeasure = 1

            Weight = math.nan

        return Weight
          
    
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
#           logging.error(': Relay ', str(self.order), ' initialization failure.')
            print("err")    
                

    def on(self):
        try:
            self.relay.on()
            self.state = 1
            self.errorOn = 0
        except:
            if self.errorOn == 0:
#                 logging.error(': Relay ', str(self.order), ' failure.')
                self.errorOn = 1

    def off(self):
        try:
            self.relay.off()
            self.state = 0
            self.erroOff = 0
        except:
            if self.erroOff == 0:
#               logging.error(': Relay ', str(self.order), ' failure.')
                self.erroOff = 1

    def toggle(self):
        if self.state == 0:
            self.on()
        else:
            self.off()