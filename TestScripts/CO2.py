import time
import seeed_sgp30
from grove.i2c import Bus

sgp30 = seeed_sgp30.grove_sgp30(Bus(1)) #The default on the raspberry pie is 1, so you can also use Bus()

while True:
    data = sgp30.read_measurements()
    co2_eq_ppm, tvoc_ppb = data.data
    print("\r  tVOC = {} ppb CO2eq = {} ppm  ".format(tvoc_ppb, co2_eq_ppm))
    time.sleep(1)