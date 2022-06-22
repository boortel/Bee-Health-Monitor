import time
import sys
import os

import seeed_sgp30
from grove.i2c import Bus

def main():
    sgp30 = seeed_sgp30.grove_sgp30(Bus(1)) #The default on the raspberry pie is 1, so you can also use Bus()

    while True:
        data = sgp30.read_measurements()
        co2_eq_ppm, tvoc_ppb = data.data
        print("\r  tVOC = {} ppb CO2eq = {} ppm  ".format(tvoc_ppb, co2_eq_ppm))
        time.sleep(0.01)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)