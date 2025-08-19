import os
import csv
import time
import json
import psutil

import logging
import datetime
import configparser

from Camera import eventCamera_capture
from CameraThread import CameraThread, eventCameraThread_run
from SensorsThread import SensorsThread, eventSensorsThread_run

#from BeeCounter.BeeCounterThread import eventBeeCounterRead, queueBeeCounterRead

def main():

    # Wait two minutes to prevent a multiple restart
    #time.sleep(120)

    # Get current time
    now = datetime.datetime.now()
    timeString = now.strftime("%Y%m%d_%H%M")
    
    # Set the rst times, the second ensures a small interval to perform rst
    #t_rst1 = datetime.time(hour = 23, minute = 50)
    #t_rst2 = datetime.time(hour = 23, minute = 52)
    t_rst1 = datetime.time(hour = 13, minute = 0)
    t_rst2 = datetime.time(hour = 13, minute = 2)

    ## Open and load the ini file
    base_path = os.path.dirname(os.path.realpath(__file__))
    cfg_path = os.path.join(base_path, 'BeeLogger.ini')

    cfg = configparser.ConfigParser()

    with open(cfg_path) as iniFile:
        cfg.read_file(iniFile)
        usb_path = None
        log_path = 'log/Log_' + timeString

        driveName = cfg.get('General', 'driveName', fallback = 'NaN')
        
        # Search for usb path if present
        for part in psutil.disk_partitions():
            if part.mountpoint.startswith('/media/vcelkator/'):
                mount_folder = os.path.basename(part.mountpoint)
                if mount_folder == driveName or mount_folder.startswith(driveName):
                    usb_path = part.mountpoint
                    break
            
        # Create the log directory and its structure if it not exists yet. Log to drive or to rPi if drive is not present.
        if driveName != 'NaN' and usb_path:
            log_path = os.path.join(usb_path, log_path)
            cfg_path = os.path.join(usb_path, 'BeeLogger.ini')
        else:
            log_path = os.path.join(base_path, log_path)
        
        if not os.path.exists(log_path):
            os.makedirs(log_path)

    # Initialize program logging
    logging.basicConfig(filename = os.path.join(log_path, 'ProgramLog.txt'),  level=logging.INFO, format='(%(asctime)s %(threadName)-10s %(levelname)-7s) %(message)s',)
    
    if driveName == 'NaN':
        logging.warning(': USB drive name is not set, saving to the default path.')

    
    # Read the CFG path from drive or local
    with open(cfg_path) as iniFile:
        cfg.read_file(iniFile)
        
        # Set the measurement period
        periodSensor = cfg.getint('Sensors', 'period_threadSensors')
        
        # Get rst enable and log stop flags
        rstEn = cfg.getboolean('General', 'rstEn')
        logStop = cfg.getboolean('General', 'logStop')

        # Initialize microphone
        recordTime = cfg.getint('Sensors', 'recordTime')
        
        ## Set the camera capture on, off and rst times, convert values to datetime
        lightOn_hour = cfg.getint('General', 'lightOn_hour')
        lightOn_minute = cfg.getint('General', 'lightOn_minute')

        lightOff_hour = cfg.getint('General', 'lightOff_hour')
        lightOff_minute = cfg.getint('General', 'lightOff_minute')
        
        t_on = datetime.time(hour = lightOn_hour, minute = lightOn_minute)
        t_off = datetime.time(hour = lightOff_hour, minute = lightOff_minute)
        
        if t_on > t_off:
            logging.error(': Capture on time is higher than the off time.')
            return -1


        ## Set the logging stop time and flag, convert values to datetime
        logOff_year = cfg.getint('General', 'logOff_year')
        logOff_month = cfg.getint('General', 'logOff_month')
        logOff_day = cfg.getint('General', 'logOff_day')
        logOff_hour = cfg.getint('General', 'logOff_hour')
        logOff_minute = cfg.getint('General', 'logOff_minute')
        
        t_stop = datetime.datetime(year = logOff_year, month = logOff_month, day = logOff_day, hour = logOff_hour, minute = logOff_minute)
        
        if logStop and now > t_stop:
            logging.error(': Stop time is smaller than the current time.')
            return -1
        
        # Check if sensor period is greater or equal to record time
        periodSensor = config.getint('Sensors', 'period_threadSensors')
        recordTime = config.getint('Sensors', 'recordTime')
        
        if periodSensor < recordTime:
            logging.error(': Sensor period has to be greater than the record time.')
            return -1
    
    # Create and run the camera and sensors threads
    #cam = CameraThread(name = 'CamThread', baseLog = log_path, config = cfg)
    sens = SensorsThread(name = 'SensThread', baseLog = log_path, config = cfg)
    sens.start()
    
    # Control the threads run and the camera capturing
    rpi_rst = False
    rpi_off = False
    
    while True:
        t_now = datetime.datetime.now()
        t_capture = datetime.time(hour=t_now.hour, minute=t_now.minute, second=t_now.second)

        # Turn on and off the camera capture together with the light
        if t_capture >= t_on and t_capture < t_off:
            eventCamera_capture.set()
            # TODO: Turn the light on
        else:
            eventCamera_capture.clear()
            # TODO: Turn the light off

        # Stop the logging if the stop flag and time are set
        if logStop and t_now >= t_stop: #and not(eventSensorThread_measure.is_set()):
            rpi_off = True
            break

        # Restart the rPi in the desired time if set
        if rstEn and t_capture >= t_rst1 and t_capture <= t_rst2:# and not(eventSensorThread_measure.is_set()):
            rpi_rst = True
            break
            
        time.sleep(0.1)
        
    # Close all events and running threads, turn the light off
    eventCamera_capture.clear()
    time.sleep(2)
    eventCameraThread_run.clear()
    
    eventSensorsThread_run.clear()
    sens.stop()
    time.sleep(2)
    
    # TODO Turn the light off
    
    # Turn off or rst the rPi
    if rpi_off:
        logging.info(': Logging was stopped after set time.')
        os.system('sudo shutdown -h now')
    elif rpi_rst:
        logging.info(': System is being restarted.')
        os.system('sudo reboot')
    else:
        logging.info(': Turning rPi off from unknown reasons.')
        os.system('sudo shutdown -h now')
    
## Run the main function
if __name__ == '__main__':
    main()
