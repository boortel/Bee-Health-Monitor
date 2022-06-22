import time
import sys
import os

from grove.grove_light_sensor_v1_2 import GroveLightSensor

def main():
    # connect to analog pin 0(slot A0)
    pin = 0
    sensor = GroveLightSensor(pin)
    print('Detecting light...')
    
    while True:
        print('Light value: {0}'.format(sensor.light))
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)