import time
import picamera

with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    camera.start_preview()
    camera.start_recording('my_video.h264')
    time.sleep(0.5)
    for x in range(0,50):
        camera.zoom=(x/100.,x/100.,0.5,0.5)
        time.sleep(0.1)

    time.sleep(2)

    for x in range(1,100):
        camera.zoom=(0,0,x/100.,x/100.)
        time.sleep(0.1)
    camera.stop_recording()