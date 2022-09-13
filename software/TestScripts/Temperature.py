import time
import sys
import os

import seeed_dht

def main():
    # for DHT11 the type is '11', for DHT22 the type is '22'
    sensor = seeed_dht.DHT("11", 16)

    while True:
        humi, temp = sensor.read()
        print('DHT{0}, humidity {1:.1f}%, temperature {2:.1f}*'.format(sensor.dht_type, humi, temp))
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