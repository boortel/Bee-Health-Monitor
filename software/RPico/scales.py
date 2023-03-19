from hx711 import HX711
from utime import sleep_us


class Scales(HX711):
    def __init__(self, d_out, pd_sck):
        super(Scales, self).__init__(d_out, pd_sck)
        self.offset = -146500

    def reset(self):
        self.power_off()
        self.power_on()

    def tare(self):
        self.offset = self.read()

    def raw_value(self):
        return self.read() - self.offset

    def stable_value(self, reads=5, delay_us=5):
        values = []
        for _ in range(reads):
            values.append(self.raw_value())
            sleep_us(delay_us)
        return self._stabilizer(values)

    @staticmethod
    def _stabilizer(values, deviation=10):
        weights = []
        for prev in values:
            try:
                weights.append(sum([1 for current in values if abs(prev - current) / (prev / 100) <= deviation]))
            except:
                return math.nan
        return sorted(zip(values, weights), key=lambda x: x[1]).pop()[0]

"""
if __name__ == "__main__":
    scales = Scales(d_out=18, pd_sck=19)
    scales.tare()
    while 1:
        val = scales.raw_value()
        print(val)
    scales.power_off()
"""