import utime
import sys
import select
import os

from machine import Pin, PWM

from SensorThread import SensorThread
from SensorThread import eventSensorThread_run
import _thread

import time

FPS = 3 #or 6
Period = 1000 / FPS
current_time = time.time_ns() // 1000000
old_time = current_time

color = 0

led = Pin(25, Pin.OUT)
led.value(1)

# Set up the poll object
poll_obj = select.poll()
poll_obj.register(sys.stdin, select.POLLIN)

FlashingEnable=False

PWM_IR = PWM(Pin(16))
PWM_Tyr = PWM(Pin(17))
PWM_W = PWM(Pin(20))
button = Pin(21, Pin.IN, Pin.PULL_DOWN)

PWM_IR.freq (5000)
PWM_Tyr.freq (5000)
PWM_W.freq (5000)
intensity=50000#1000#65535
ports_set = 0

v=""
ButtonState=False
OldButtonState=False

if __name__ == "__main__":  
    while True:
        current_time=time.time_ns() // 1000000
        ButtonState=button.value()
        if ButtonState and not OldButtonState:
            print("STOP")
            FlashingEnable=False
            try:
                eventSensorThread_run.release()
            except:
                pass
        OldButtonState=ButtonState
        poll_results = poll_obj.poll(1) # the '1' is how long it will wait for message before looping again (in microseconds)
        #print(FlashingEnable)
        if FlashingEnable:
            if current_time-old_time>=Period:
                old_time=current_time
                color+=1
                if color >= 3:
                    color = 0
                if color == 0:
                    PWM_IR.duty_u16(intensity)
                    PWM_Tyr.duty_u16(0)
                    PWM_W.duty_u16(0)
                    print("The IR color was set")
                elif color == 1:
                    PWM_IR.duty_u16(0)
                    PWM_Tyr.duty_u16(intensity)
                    PWM_W.duty_u16(0)
                    print("The Tur color was set")
                elif color == 2:
                    PWM_IR.duty_u16(0)
                    PWM_Tyr.duty_u16(0)
                    PWM_W.duty_u16(intensity)
                    print("The W color was set")
        else:
            PWM_IR.duty_u16(0)
            PWM_Tyr.duty_u16(0)
            PWM_W.duty_u16(0)
                
        if poll_results:
            # Read the data from stdin (read data coming from PC)
            v = sys.stdin.readline().strip()
            #print(v)
        #else:
            if v == "start":
                FlashingEnable=True
                if ports_set:
                    sen.flush = 1
                    led.value(0)
                else:
                    sen = SensorThread(name = 'SensThread')
                    
                if not eventSensorThread_run.locked():
                    eventSensorThread_run.acquire()
                _thread.start_new_thread(sen.run, ())
            elif "Ports:" in v:
                v = v[6:]
                ports = v.split(";")
                try:
                    sen = SensorThread(name = 'SensThread',port_HX711 = int(ports[0]), port_light = int(ports[1]))
                except:
                    sen = SensorThread(name = 'SensThread')
                ports_set = 1
            elif v == "send data":
                sen.sendData = 1
#             elif "ILLUminATion:" in v: #yes minion
#                 v = v[13:]
#                 mess = v.split(";")
#                 color = mess[0]
#                 intensity = int(mess[1])
#                 if color == "IR":
#                     PWM_IR.duty_u16(intensity)
#                     PWM_Tyr.duty_u16(0)
#                     PWM_W.duty_u16(0)
#                 elif color == "Tur":
#                     PWM_IR.duty_u16(0)
#                     PWM_Tyr.duty_u16(intensity)
#                     PWM_W.duty_u16(0)
#                 elif color == "W":
#                     PWM_IR.duty_u16(0)
#                     PWM_Tyr.duty_u16(0)
#                     PWM_W.duty_u16(intensity)
#                print("The " + color + " color was set")
            elif v == "STOP ILLUminATion":
                FlashingEnable=False
                try:
                    eventSensorThread_run.release()
                except:
                    pass
            elif v == "reset":
                FlashingEnable=False
                try:
                    eventSensorThread_run.release()
                except:
                    pass
                print("ready")

