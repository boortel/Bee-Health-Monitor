import time
import seeed_dht
# for DHT11 the type is '11', for DHT22 the type is '22'
# Teplomer se pripojuje k digitalnim vstupum - one wire sbernice!!!
sensor = seeed_dht.DHT("11", 16)

while True:
    humi, temp = sensor.read()
    print('DHT{0}, humidity {1:.1f}%, temperature {2:.1f}*'.format(sensor.dht_type, humi, temp))
    time.sleep(1)