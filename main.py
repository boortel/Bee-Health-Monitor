import configparser
import datetime
import logging
import time
import os

from SensorThread import SensorThread
from CameraThread import CameraThread

from Sensors import Relay

from Camera import setCaptureStatus
from CameraThread import stopCamThread
from SensorThread import stopSenThread

def main():
    # Initialize program logging
    logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-5s) %(message)s',)

    # Open the ini file
    cfg = configparser.ConfigParser()
    cfg.read('BeeLogger.ini')

    # Get current time
    now = datetime.datetime.now()
    timeStamp = now.strftime("%y%m%d_%H%M%S")

    # Set the camera capture on and off times
    lightOn_hour = cfg.getint('General', 'lightOn_hour')
    lightOn_minute = cfg.getint('General', 'lightOn_minute')

    lightOff_hour = cfg.getint('General', 'lightOff_hour')
    lightOff_minute = cfg.getint('General', 'lightOff_minute')

    t_on = datetime.time(hour=lightOn_hour, minute=lightOn_minute)
    t_off = datetime.time(hour=lightOff_hour, minute=lightOff_minute)

    if t_on > t_off:
        logging.error(timeStamp + ': Capture on time is higher than the off time.')
        return

    # Set the logging stop time and flag
    logOff_year = cfg.getint('General', 'logOff_year')
    logOff_month = cfg.getint('General', 'logOff_month')
    logOff_day = cfg.getint('General', 'logOff_day')
    logOff_hour = cfg.getint('General', 'logOff_hour')
    logOff_minute = cfg.getint('General', 'logOff_minute')

    logStop = cfg.getboolean('General', 'logStop')
    t_stop = datetime.datetime(year=logOff_year, month=logOff_month, day=logOff_day, hour=logOff_hour, minute=logOff_minute)

    if logStop and now > t_stop:
        logging.error(timeStamp + ': Stop time is smaller than the current time.')
        return

    # Initialize the relay object
    relay = Relay(1, 5)

    # Create the log directory and its structure if it not exists yet
    timeString = now.strftime("%y%m%d_%H%M")

    # Log session base path
    driveName = cfg.get('General', 'driveName')
    
    if driveName:
        logPath = '/media/pi/' + driveName + '/log/Log_' + timeString
    else:
        logPath = '/log/Log_' + timeString
        now = datetime.datetime.now()
        timeStamp = now.strftime("%y%m%d_%H%M%S")
        logging.warning(timeStamp + ': USB drive name is not set, saving to the SD.')

    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Create the sensor and camera thread
    sen = SensorThread(name = 'sensor', baseLog = logPath, config = cfg)
    cam = CameraThread(name = 'camera', baseLog = logPath, config = cfg)

    # Run the threads
    sen.start()
    cam.start()

    log = True

    # Control the threads run and the camera capturing
    while log:
        t_now = datetime.datetime.now()
        t_capture = datetime.time(hour=t_now.hour, minute=t_now.minute, second=t_now.second)

        # Turn on and off the camera capture together with the light
        if t_capture >= t_on and t_capture < t_off:
            setCaptureStatus(True)
            relay.on()
        else:
            setCaptureStatus(False)
            relay.off()

        # Stop the logging if the stop flag and time are set
        if logStop and t_now >= t_stop:
            stopCamThread(relay)
            stopSenThread()
            log = False
        
        time.sleep(0.1)


# Run the main function
if __name__ == '__main__':
    main()