import time
from grove.factory import Factory

relay = Factory.getGpioWrapper("Relay",5)
while True:
    relay.on()
    time.sleep(2)
    relay.off()
    time.sleep(5)