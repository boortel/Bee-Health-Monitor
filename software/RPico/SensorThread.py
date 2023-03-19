import machine
import _thread
import time
import time
import math

# Import the sensors
from sensors_pico import DHT11, LightS, Relay, SHT31, Sgp30, hx_711, DHT21

# Global variable to stop sensor logging
sensLogStatus = True

# Event to stop the SensorThread internal loop and to lock the measurement
eventSensorThread_run = _thread.allocate_lock()
# ♥eventSensorThread_measure = _thread.allocate_lock()

# Sensor handle thread
class SensorThread(object):
    def __init__(self, name, port_HX711=18, port_light=0):
#         ♥super(SensorThread,self).__init__()
        self.name = name
        self.errorLog = 0
        self.periodSensor = 0.9
        self.sendData = 0
        self.flush = 0
        
        #Set ports

        # Initialize the sensors objects
        self.DHT21_1 = DHT21(1)
        self.DHT21_2 = DHT21(2)
        self.SHT31_1 = SHT31(1)
        self.Light_1 = LightS(1, port_light)
        self.HX711_1 = hx_711(1, port_HX711, 19)
#         #self.HX711_1 = hx_711(1,18)


        # Initialize and run the SGP30Thread
        self.SGP30_1 = Sgp30(1)

        eventSensorThread_run.acquire()
        

    def run(self):
        # Wait the first period to ensure a correct sampling after reset
        diff = 0
        HumIn_1_arr = 0
        TempIn_1_arr = 0
        HumIn_2_arr = 0
        TempIn_2_arr = 0
        TempOut_arr = 0
        HumOut_arr = 0
        PressOut_arr = 0
        Light_arr = 0
        co2_eq_ppm_arr = 0
        tvoc_ppb_arr = 0
        weight = 0
        i =0
        i_weight = 0
        
        # This loop is run until stopped from main
        while eventSensorThread_run.locked():
            # Get the start time
            t1 = time.time()

            if self.flush:
                diff = 0
                HumIn_1_arr = 0
                TempIn_1_arr = 0
                HumIn_2_arr = 0
                TempIn_2_arr = 0
                TempOut_arr = 0
                HumOut_arr = 0
                PressOut_arr = 0
                Light_arr = 0
                co2_eq_ppm_arr = 0
                tvoc_ppb_arr = 0
                weight_arr = 0
                i =0
                i_weight = 0
                self.flush = 0

            # DHT11 - inner temperature and humidity
            HumIn_1, TempIn_1 = self.DHT21_1.measure()
            HumIn_1_arr = HumIn_1_arr+HumIn_1
            TempIn_1_arr = TempIn_1_arr+TempIn_1
            
            HumIn_2, TempIn_2 = self.DHT21_2.measure()
            HumIn_2_arr = HumIn_2_arr+HumIn_2
            TempIn_2_arr = TempIn_2_arr+TempIn_2
            
            # SHT31 - outer temperature, humidity and pressure
            TempOut, HumOut, PressOut = self.SHT31_1.measure()
            TempOut_arr = TempOut_arr+TempOut
            HumOut_arr = HumOut_arr+HumOut
            PressOut_arr = PressOut_arr+PressOut
            
            # Light sensor value
            Light = self.Light_1.measure()
            Light_arr = Light_arr+Light
            
            co2_eq_ppm, tvoc_ppb = self.SGP30_1.measure()
            co2_eq_ppm_arr = co2_eq_ppm_arr+co2_eq_ppm
            tvoc_ppb_arr = tvoc_ppb_arr+tvoc_ppb
            
            weight = self.HX711_1.measure()
            if weight != math.nan:
                weight_arr = weight_arr + weight
                i_weight = i_weight+1
            
            i = i+1
            
                
            if self.sendData == 1:
                data ="Data:" + str(co2_eq_ppm_arr/i)+";"+str(tvoc_ppb_arr/i)+";"+str(TempIn_1_arr/i)+";"+str(HumIn_1_arr/i)+";"+str(TempIn_2_arr/i)+";"+str(HumIn_2_arr/i)+";"+str(TempOut_arr/i)+";"+str(HumOut_arr/i)+";"+str(PressOut_arr/i)+";"+str(Light_arr/i)+";"+str(weight_arr/i_weight)
                print(data)
                HumIn_1_arr = 0
                TempIn_1_arr = 0
                HumIn_2_arr = 0
                TempIn_2_arr = 0
                TempOut_arr = 0
                HumOut_arr = 0
                PressOut_arr = 0
                Light_arr = 0
                co2_eq_ppm_arr = 0
                tvoc_ppb_arr = 0
                weight_arr = 0
                i=0
                i_weight = 0
                self.sendData = 0


            # Get the end time and the time difference to sleep
            t2 = time.time()
            diff = t2 - t1

            # Sleep till the next sensor read period
            if diff < self.periodSensor:

                while (diff < self.periodSensor) and sensLogStatus:
                    t2 = time.time()
                    diff = t2 - t1
                    
            else:
                print(': Set period time was exceeded during the current iteration.') 
