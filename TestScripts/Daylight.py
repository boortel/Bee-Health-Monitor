import time
from grove.grove_light_sensor_v1_2 import GroveLightSensor

# connect to analog pin 0(slot A0)
pin = 0
sensor = GroveLightSensor(pin)
print('Detecting light...')
while True:
    print('Light value: {0}'.format(sensor.light))
    time.sleep(1)