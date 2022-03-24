from picamera import PiCamera
from time import sleep

camera = PiCamera()

sleep(2)

camera._set_zoom([1.0, 1.0, 0.5, 0.5])

camera.start_preview()
sleep(10)
camera.stop_preview()

temp = camera._get_zoom()
print(temp)