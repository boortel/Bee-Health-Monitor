from sgp30 import SGP30 

class grove_sgp30(object):
    def __init__(self, bus):
        self.baseline_conf = "/tmp/SGP30_baseline"
        self.sgp = Sgp30(bus, baseline_filename = self.baseline_conf)
        self.sgp.i2c_geral_call()
        self.sgp.read_features()
        serial = self.sgp.read_serial()
        print("SGP30 SERIAL: {}".format(serial.raw))

        self.sgp.init_sgp()
    def read_measurements(self):
        return self.sgp.read_measurements()