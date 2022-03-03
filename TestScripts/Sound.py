
import time
from grove.grove_sound_sensor import GroveSoundSensor
# connect to analog pin 2(slot A2)

pin = 2
sensor = GroveSoundSensor(pin)
print('Detecting sound...')

while True:
    print('Sound value: {0}'.format(sensor.sound))
    time.sleep(.3)