

import configparser
import datetime
import logging
import time
import os
import serial.tools.list_ports
import csv
import paho.mqtt.client as mqtt
import json

from CameraThread import CameraThread

from Sensors import Relay, RPico

from Camera import eventCamera_capture
from CameraThread import eventCameraThread_run
from Microphone import Microphone
import ImageProcessorThread 

from BeeCounter.BeeCounterThread import eventBeeCounterRead, queueBeeCounterRead

def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code {}".format(rc))
#def on_message():
#    logging.info("Message sent to DB")

def main():

    ## Wait two minutes to prevent a multiple restart
    time.sleep(1)#120
    
    ImageProcessorThread.ReqColor=0

    #Connect to Raspberry Pico
    pico = RPico()

    MQTT_SERVER = "address_of_server"
    MQTT_PATH = "name_of_topic"

    client = mqtt.Client()
    client.on_connect = on_connect

    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

    client.username_pw_set("username", "password")
    
    ## Get current time
    now = datetime.datetime.now()
    timeString = now.strftime("%Y%m%d_%H%M")

    ## Open the ini file
    base_path = os.path.dirname(os.path.realpath(__file__))
    cfg_path = os.path.join(base_path, 'BeeLogger.ini')

    cfg = configparser.ConfigParser()
    with open(cfg_path) as f:
        cfg.read_file(f)
        #cfg.read(cfg_path)
 
        ## Create the log directory and its structure if it not exists yet
    
        # Log session base path
        driveName = cfg.get('General', 'driveName', fallback = 'NaN')
        
        ## Set the camera capture on, off and rst times
        lightOn_hour = cfg.getint('General', 'lightOn_hour')
        lightOn_minute = cfg.getint('General', 'lightOn_minute')

        lightOff_hour = cfg.getint('General', 'lightOff_hour')
        lightOff_minute = cfg.getint('General', 'lightOff_minute')

        # Get rst enable flag
        rstEn = cfg.getboolean('General', 'rstEn')

        ## Set the logging stop time and flag
        logOff_year = cfg.getint('General', 'logOff_year')
        logOff_month = cfg.getint('General', 'logOff_month')
        logOff_day = cfg.getint('General', 'logOff_day')
        logOff_hour = cfg.getint('General', 'logOff_hour')
        logOff_minute = cfg.getint('General', 'logOff_minute')
    
        # Set the measurement period
        periodSensor = cfg.getint('Sensors', 'period_threadSensors')

        logStop = cfg.getboolean('General', 'logStop')

        # Initialize microphone
        recordTime = cfg.getint('Sensors', 'recordTime')

        port_HX711 = cfg.getint('Sensors', 'port_HX711')
        port_light = cfg.getint('Sensors', 'port_LightS_1')
    

    if driveName != 'NaN':
        #logPath = '/media/pi/' + driveName + '/log/Log_' + timeString #sem nedokaze zapisovat
        logPath = '/home/pi/Documents/Log' + driveName + '/log/Log_' + timeString
        driveSet = False

    #    cfg_path = '/media/pi/' + driveName + '/BeeLogger.ini'
    #    # Reload the ini file from USB drive if present
    #    if os.path.exists(cfg_path):
    #        cfg.read(cfg_path)

    else:
        logPath = 'log/Log_' + timeString
        logPath = os.path.join(base_path, logPath)
        driveSet = True

    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Initialize program logging
    logging.basicConfig(filename = logPath + '/ProgramLog.txt',  level=logging.DEBUG, format='(%(asctime)s %(threadName)-10s %(levelname)-7s) %(message)s',)
    #logging.basicConfig(level=logging.DEBUG, format='(%(asctime)s %(threadName)-10s %(levelname)-7s) %(message)s',)

    # Log warning message if the drive not set
    if driveSet:
        logging.warning(': USB drive name is not set, saving to the default path.')

    t_on = datetime.time(hour = lightOn_hour, minute = lightOn_minute)
    t_off = datetime.time(hour = lightOff_hour, minute = lightOff_minute)

    # Set the rst times, the second ensures a small interval to perform rst
    t_rst1 = datetime.time(hour = 23, minute = 50)
    t_rst2 = datetime.time(hour = 23, minute = 52)

    if t_on > t_off:
        logging.error(': Capture on time is higher than the off time.')
        return -1

    t_stop = datetime.datetime(year = logOff_year, month = logOff_month, day = logOff_day, hour = logOff_hour, minute = logOff_minute)

    # Initialize microphone
    microphone = Microphone(recordTime, logPath)

    if logStop and now > t_stop:
        logging.error(': Stop time is smaller than the current time.')
        return -1

    #Connect to MQTT broker
    try:
        client.connect(MQTT_SERVER, 8883)
    except:
        logging.error(": Could not connect to client")

    ## Initialize the relay
    #relay = Relay(1, 5) # LED strip
    # Initialize the red LED
    redLED = Relay(3, 24)

    ## Create the camera thread
    print("Tu zacina kamera")
    cam = CameraThread(name = 'CamThread', baseLog = logPath, config = cfg)

    ## Run the camera thread
    cam.start()

    # Open the log file and create header
    try:
        fileName = logPath + '/SensorLog' + '.csv'

        # Open the csv and write header
        row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 
            'TempIn_1 (degC)', 
            'HumIn_1 (%)', 'TempIn_2 (degC)', 'HumIn_2 (%)', 'TempOut (dgC)', 'HumOut (%)', 'Pressure (hPa)', 'Light (-)', 'Weight (-)', 'BeeIn (-)', 'BeeOut (-)']
        with open(fileName, 'w', newline = '') as csvFile:
            writer = csv.writer(csvFile, delimiter =';')
            writer.writerow(row)
    except:
        logging.error(': Initialization of the log file failed.')

    log = True
    client.loop_start()
    diff = 0
    last_message = ""

    pico.set_ports(port_HX711,port_light)
    #Start data acquisition in Raspberry Pico
    pico.start()

    data_logged = True
    ## Control the threads run and the camera capturing
    while log:
        if data_logged:
            t1 = time.time()
            data_logged=False
        
        t_now = datetime.datetime.now()
        t_capture = datetime.time(hour=t_now.hour, minute=t_now.minute, second=t_now.second)

        # Turn on and off the camera capture together with the light
        if t_capture >= t_on and t_capture < t_off: 
            pico.set_lights(ImageProcessorThread.ReqColor)
            eventCamera_capture.set()
        else:
            eventCamera_capture.clear()

        # Stop the logging if the stop flag and time are set
        if logStop and t_now >= t_stop: #and not(eventSensorThread_measure.is_set()):
            eventCamera_capture.clear()
            time.sleep(2)

            eventCameraThread_run.clear()
            
            #eventSensorThread_run.clear()

            logging.info(': Logging was stopped after set time.')

            log = False
            #relay.off()
            pico.clear_lights()
            os.system('sudo shutdown -h now')

        t2 = time.time()
        diff = t2 - t1
        if diff>=periodSensor:
            # Toggle the red LED
            redLED.toggle()

            line = pico.send_data()
            data_logged=1

        line = pico.read_line()
        if len(line)>0:
            if "Data:" in line:
                #Splitting sensor data from raspberry pico
                line = line[5:].split(";")
                co2_eq_ppm = float(line[0])
                tvoc_ppb = float(line[1])
                TempIn_1 = float(line[2])
                HumIn_1 = float(line[3])
                TempIn_2 = float(line[4])
                HumIn_2 = float(line[5])
                TempOut =float(line[6])
                HumOut = float(line[7])
                PressOut = float(line[8])
                Light = float(line[9])
                Weight = float(line[10])

                #Timestamp for sensor data 
                now = datetime.datetime.now()
                timeStampM = now.strftime("%Y.%m.%d %H:%M:%S")
                try:
                    eventBeeCounterRead.set()
                    BeeIn, BeeOut = queueBeeCounterRead.get(timeout = 5)
                except:
                    BeeIn = 0
                    BeeOut = 0
                #Creating json string to send to database
                json_str = json.dumps([{"Timestamp":now.timestamp(),
                                        "co2_eq_ppm":float(line[0]),
                                        "tvoc_ppb":float(line[1]),
                                        "TempIn_1":float(line[2]),
                                        "HumIn_1":float(line[3]),
                                        "TempIn_2":float(line[4]),
                                        "HumIn_2":float(line[5]),
                                        "TempOut":float(line[6]),
                                        "HumOut":float(line[7]),
                                        "PressOut":float(line[8]),
                                        "Light":float(line[9]),
                                        "Weight":float(line[10]),
                                        "BeeIn":BeeIn,
                                        "BeeOut":BeeOut}])

                #Check if connected to broker, if not store the message and send it next time
                try:
                    if (client.is_connected()):
                        if len(last_message)>0:
                            client.publish(MQTT_PATH,last_message)
                            logging.info(": Last message sent to DB")
                            last_message = ""
                        client.publish(MQTT_PATH,json_str)
                        logging.info(": Message sent to DB") 
                    else:
                        client.connect(MQTT_SERVER, 8883)
                        client.publish(MQTT_PATH,json_str)
                except:
                    last_message = json_str
                    logging.info(": Could not send message to DB")
                        
                # Create log
                row = [f'{timeStampM:s}', f'{co2_eq_ppm}',  f'{tvoc_ppb}', f'{float(TempIn_1):.2f}', f'{float(HumIn_1):.2f}', f'{float(TempIn_2):.2f}', f'{float(HumIn_2):.2f}',f'{float(TempOut):.2f}', f'{float(HumOut):.2f}', f'{float(PressOut):.2f}', f'{Light}', f'{Weight}',f'{BeeIn}', f'{BeeOut}']

                try:    
                    with open(fileName, 'a', newline = '') as csvFile:

                        writer = csv.writer(csvFile, delimiter =';')
                        writer.writerow(row)

                    logging.info(': Sensor data were writen to the log.')
                    errorLog = 0
                except:
                    if errorLog == 0:
                        logging.error(': Writing to log file failed.')
                        errorLog = 1


                microphone.record()

                redLED.off()

            elif "STOP" in line:
                pico.clear_lights()
                eventCamera_capture.clear()
                time.sleep(2)
                eventCameraThread_run.clear()
                pico.close()
                log = False
            
            elif "color was set" in line:
                line = line.split(" ")
                if "W" in line[1]:
                    cam.SetColor=0
                    ImageProcessorThread.SetColor=0
                elif "IR" in line[1]:
                    cam.SetColor=1
                    ImageProcessorThread.SetColor=1
                elif "Tur" in line[1]:
                    cam.SetColor=2
                    ImageProcessorThread.SetColor=2
                #print(line[1])
            
            else:
                logging.error(line)

        # Restart the rPi in the desired time if set
        if rstEn and t_capture >= t_rst1 and t_capture <= t_rst2:# and not(eventSensorThread_measure.is_set()):
            pico.clear_lights()
            eventCamera_capture.clear()
            time.sleep(2)

            eventCameraThread_run.clear()
            pico.close()
            logging.info(': System is being restarted.')

            os.system('sudo reboot')
        
        time.sleep(0.1)

    #client.loop_stop()
    
## Run the main function
if __name__ == '__main__':
    main()
