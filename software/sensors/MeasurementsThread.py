import time
import queue
import logging
import threading

from numpy import NaN

# Import the sensor libraries
from sensors.sgp30 import SGP30
from sensors.dht20 import DHT20
from sensors.sht31 import SHT31
from sensors.gy302 import GY302
import sensors.piqmp6988SM as QMP6988

# Event to stop the SGP30Thread internal loop
eventMeasurements_run = threading.Event()

# Queue and its control event to send SGP30 data
BUFF = 5
queueMeasurementAVG = queue.Queue(BUFF)
eventMeasurementAVG_read = threading.Event()

# Configuration of the QMP6988 atmospheric pressure sensor
config = {
    'temperature' : QMP6988.Oversampling.X4.value,
    'pressure' :    QMP6988.Oversampling.X32.value,
    'filter' :      QMP6988.Filter.COEFFECT_32.value,
    'mode' :        QMP6988.Powermode.NORMAL.value
}

# SGP30 sensor has to be run every 1s in background to ensure a correct online calibration
# This thread computes the floatig average of all sensor values over the set measurement period

# Sensor handle thread
class MeasurementsThread(threading.Thread):
    def __init__(self):
        super(MeasurementsThread,self).__init__()
        self.name = 'MeasThread'
        
        eventMeasurements_run.set()
        
        # Create the sensor objects
        self.sht31 = SHT31(0x01, 0x44)
        self.dht20 = DHT20(0x01, 0x38)
        self.sgp30 = SGP30(0x01, 0x58)
        #self.gy302 = GY302(0x01, 0x23)
        self.qmp = QMP6988.PiQmp6988(0x01, config)
        
        # Initialize the sensors
        if not self.sht31.begin():
            logging.error(': SHT31 sensor initialization failed') 
        if not self.dht20.begin():
            logging.error(': DHT20 sensor initialization failed')
        if not self.sgp30.begin():
            logging.error(': SGP30 sensor initialization failed')
        #if not self.gy302.begin():
        #    logging.error(': GY302 sensor initialization failed")
        

    def run(self):
        
        # Define the empty lists for floating average over the measurement period
        co2_buffer = []
        voc_buffer = []
        
        TempIn_buffer = []
        HumIn_buffer = []
        
        TempOut_buffer = []
        HumOut_buffer = []
        
        LightOut_buffer = []
        PressOut_buffer = []
        
        # Flag to control period of CO2 (every 1s) and others (every 2s) readouts
        even_second = False
        
        # This loop is run until stopped from SensorThread
        while eventMeasurements_run.is_set():
            
            # Get the measurement start time
            measurement_duration_start = time.time()
            
            # Toggle the even_second flag
            if even_second:
                even_second = False
            else:
                even_second = True
    
            # Get the data from SGP30
            co2_eq_ppm, tvoc_ppb, sgp_error = self.sgp30.get_air_quality()
            if sgp_error:
                co2_eq_ppm = NaN
                tvoc_ppb = NaN
                logging.error(': SGP30 CRC error')
            
            co2_buffer.append(co2_eq_ppm)
            voc_buffer.append(tvoc_ppb)
                
            if even_second:
                # DHT20 - inner temperature and humidity
                TempIn, HumIn, dht_error = self.dht20.get_temperature_and_humidity()
                if dht_error:
                    TempIn = NaN
                    HumIn = NaN
                    logging.error(': DHT20 CRC error')
                    
                TempIn_buffer.append(TempIn)
                HumIn_buffer.append(HumIn)

                # SHT31 - outer temperature, humidity and pressure
                TempOut, HumOut, sht_err = self.sht31.get_temperature_and_humidity()
                if sht_err:
                    TempOut = NaN
                    HumOut = NaN
                    logging.error(': SHT31 CRC error')
                    
                TempOut_buffer.append(TempOut)
                HumOut_buffer.append(HumOut)
                    
                # GY302 - light intensity
                #LightOut = self.gy302.read_light()
                LightOut = 1
                if LightOut == -1:
                    LightOut = NaN
                    logging.error(': GY302 reading error')
                
                LightOut_buffer.append(LightOut)
                
                # QMP6988 - outer temperature, atmospheric pressure
                values = self.qmp.read()
                #TempOut = values['temperature']
                PressOut = values['pressure']
                if PressOut is False or PressOut is None:
                    PressOut = NaN
                    logging.error(': QMP6988 reading error')
                
                PressOut_buffer.append(PressOut)
                
            # Put the average measurements to the queue
            if eventMeasurementAVG_read.is_set():
                # Compute average over the buffers
                co2_avg = sum(co2_buffer) / len(co2_buffer) if co2_buffer else NaN
                voc_avg = sum(voc_buffer) / len(voc_buffer) if voc_buffer else NaN
                
                TempIn_avg = sum(TempIn_buffer) / len(TempIn_buffer) if TempIn_buffer else NaN
                HumIn_avg = sum(HumIn_buffer) / len(HumIn_buffer) if HumIn_buffer else NaN
                
                TempOut_avg = sum(TempOut_buffer) / len(TempOut_buffer) if TempOut_buffer else NaN
                HumOut_avg = sum(HumOut_buffer) / len(HumOut_buffer) if HumOut_buffer else NaN
                
                LightOut_avg = sum(LightOut_buffer) / len(LightOut_buffer) if LightOut_buffer else NaN
                PressOut_avg = sum(PressOut_buffer) / len(PressOut_buffer) if PressOut_buffer else NaN
                
                # Put the data to the queue
                queueMeasurementAVG.put([co2_avg, voc_avg, TempIn_avg, HumIn_avg, TempOut_avg, HumOut_avg, PressOut_avg, LightOut_avg])
                
                # Restart the buffers
                co2_buffer = []
                voc_buffer = []
                
                TempIn_buffer = []
                HumIn_buffer = []
                
                TempOut_buffer = []
                HumOut_buffer = []
                
                LightOut_buffer = []
                PressOut_buffer = []
                
                eventMeasurementAVG_read.clear()
            
            # Get the end time and the time difference to sleep
            measurement_duration_stop = time.time()
            measurement_duration = measurement_duration_stop - measurement_duration_start
            
            logging.debug(f': Script running time   : {measurement_duration:.2f} s\n')
            if (1 - measurement_duration) > 0:
                time.sleep(1 - measurement_duration)
