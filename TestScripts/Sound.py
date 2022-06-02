
import time
import sys
import os

from grove.grove_sound_sensor import GroveSoundSensor

def main():
    # connect to analog pin 2(slot A2)
    pin = 2
    sensor = GroveSoundSensor(pin)
    print('Detecting sound...')

    while True:
        print('Sound value: {0}'.format(sensor.sound))
        time.sleep(.3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)