import time
import sys
import os

from grove.factory import Factory

def main():
    relay = Factory.getGpioWrapper("Relay",5)

    while True:
        relay.on()
        time.sleep(2)
        relay.off()
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)