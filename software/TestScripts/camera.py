from picamera import PiCamera
from time import sleep

import sys
import os

def main():
    camera = PiCamera()
    sleep(2)

    try:
        camera.start_preview()
    except KeyboardInterrupt:
        camera.stop_preview()

if __name__ == '__main__':
    main()

    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)