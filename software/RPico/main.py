import utime
from machine import Pin
from SensorThread import SensorThread
from SensorThread import eventSensorThread_run
import sys
import _thread

led = Pin(25, Pin.OUT)
led.value(1)
ports_set = 0

if __name__ == "__main__":  
    while True:
        v = sys.stdin.readline().strip()
        if v == "start":
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
        elif v =="reset":
            try:
                eventSensorThread_run.release()
            except:
                pass
            print("ready")
        