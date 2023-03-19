import time
# ♥from grove.i2c import Bus
import machine
 
 
def CRC(data):
    crc = 0xff
    for s in data:
        crc ^= s
        for _ in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc

def reg_write(i2c, addr, reg, data):
    """
    Write bytes to the specified register.
    """
    
    # Construct message
    msg = bytearray()
    msg.append(data)
    
    # Write out message to register
    i2c.writeto_mem(addr, reg, msg)
    
def reg_read(i2c, addr, reg, nbytes):
    """
    Read byte(s) from specified register. If nbytes > 1, read from consecutive
    registers.
    """
    
    # Check to make sure caller is asking for 1 or more bytes
    if nbytes < 1:
        return bytearray()
    
    # Request data from specified register(s) over I2C
    data = i2c.readfrom_mem(addr, reg, nbytes)
    
    return data
 
class GroveTemperatureHumiditySensorSHT3x(object):
 
    def __init__(self, address=0x44, bus=None):
        self.address = address
 
        # I2C bus
        self.i2c = machine.I2C(1,
                  scl=machine.Pin(7),
                  sda=machine.Pin(6),
                  freq=400000)
 
    def read(self):
        # high repeatability, clock stretching disabled
        reg_write(self.i2c, self.address, 0x24, 00)
 
        # measurement duration < 16 ms
        time.sleep(0.016)
 
        # read 6 bytes back
        # Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
        data = reg_read(self.i2c, self.address, 0x00, 6)
 
        if data[2] != CRC(data[:2]):
            raise ValueError("temperature CRC mismatch")
        if data[5] != CRC(data[3:5]):
            raise ValueError("humidity CRC mismatch")
 
 
        temperature = data[0] * 256 + data[1]
        celsius = -45 + (175 * temperature / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
 
        return celsius, humidity
 
 
# ♥Grove = GroveTemperatureHumiditySensorSHT3x
 
 
# def main():
#     sensor = GroveTemperatureHumiditySensorSHT3x()
#     while True:
#         temperature, humidity = sensor.read()
#  
#         print('Temperature in Celsius is {:.2f} C'.format(temperature))
#         print('Relative Humidity is {:.2f} %'.format(humidity))
#  
#         time.sleep(1)
 
 
# if __name__ == "__main__":
#     main()