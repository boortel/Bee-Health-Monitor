import time
import logging
import serial
import os
import time
import serial.tools.list_ports

from numpy import NaN

# Import Grove stuff
from grove.factory import Factory


class RPico(object):
    # Class to control DHT11 temperature and humidity sensor
    def __init__(self):
        self.errorMeasure = 0
        self.errorIllumination=0
        self.colors=["W","IR","Tyr"]
        self.color=0
        self.intensity=32768

        try_n = 2
        port_not_binded = True
        while port_not_binded and try_n !=0:
            # Scan ports for devices
            ports = serial.tools.list_ports.comports()
            # Connect to the raspberry pico and send reset command
            for port, desc, hwid in sorted(ports):
                if ("Board CDC" in desc):
                    self.s = serial.Serial(port, 115200)
                    self.s.timeout=5
                    self.s.reset_input_buffer()
                    self.s.write(b"reset\n")
                    time.sleep(3)
                    if self.s.in_waiting > 0:
                        line = self.s.readline().decode('utf-8').rstrip()
                        if "ready" in line:
                            port_not_binded = False
            if port_not_binded:
                os.system("sudo usbreset")
                time.sleep(5)
            try_n = try_n-1

        if port_not_binded:
            os.system("sudo usbreset")
            time.sleep(120)
            os.system("sudo reboot")

    def set_ports(self,port_HX711,port_light):
        try:
            message = "Ports:{};{}\n".format(port_HX711,port_light)
            self.s.write(bytes(message,'UTF-8'))
        except:
            if self.errorMeasure == 0:
                logging.error(': Raspberry Pico set ports failure.')
                self.errorMeasure = 1

    def set_lights(self):
        try:
            mess = "ILLUminATion:{};{};\n".format(self.colors[self.color],self.intensity)
            print(mess)
            self.s.write(bytes(mess,'UTF-8'))
            self.color=self.color+1
            if self.color>=3:
                self.color=0
        except:
            if self.errorIllumination == 0:
                logging.error(': Raspberry Pico ILLUminATion failure.')
                self.errorIllumination = 1

    def clear_lights(self):
        try:
            pass
            #mess = "ILLUminATion:W;0;\n"#Program in Pico turn off other led when one is set
            #self.s.write(bytes(mess,'UTF-8'))
        except:
            if self.errorIllumination == 0:
                logging.error(': Raspberry Pico ILLUminATion failure.')
                self.errorIllumination = 1

    def send_data(self):
        try:
            self.s.write(b"send data\n")
        except:
            if self.errorMeasure == 0:
                logging.error(': Raspberry Pico measure failure.')
                self.errorMeasure = 1


    def read_line(self):
        try:
            if self.s.in_waiting > 0:
                line = self.s.readline().decode('utf-8').rstrip()
            else:
                line = ""
        except:
            if self.errorMeasure == 0:
                logging.error(': Raspberry Pico measure failure.')
                self.errorMeasure = 1
            line = ""

        return line

    def start(self):
        try:
            self.s.write(b"start\n")
            if self.s.in_waiting > 0:
                line = self.s.readline().decode('utf-8').rstrip()
                if not("Data:" in line):
                    logging.info(': '+line)
        except:
            if self.errorMeasure == 0:
                logging.error(': Raspberry Pico communication failure.')
                self.errorMeasure = 1
    
    def close(self):
        try:
            self.s.close()
        except:
            logging.error(': Error while closing Raspberry Pico.')


class Relay(object):
    # Class to control relay from RPI, not pico
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