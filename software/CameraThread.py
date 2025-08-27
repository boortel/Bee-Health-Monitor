import os                              
import time                             
import datetime                         
import logging                          
import threading                        
from typing import Tuple                

import numpy as np                      
import cv2                             
from picamera2 import Picamera2         

eventCamera_capture = threading.Event()     # SET = SNÍMÁNÍ, CLEAR = ZASTAVIT SNÍMÁNÍ
eventCameraThread_run = threading.Event()   # SET = VLÁKNO ZAPNUTO, CLEAR = UKONČIT VLÁKNO

def start_capture():                        
    eventCamera_capture.set()               # nastaví event na ON
def stop_capture():                         
    eventCamera_capture.clear()             # nastaví event na OFF

# Detektor aktuální vs. předchozí snímek
class SimpleBackgroundDetector:
    def __init__(self, diff_th: int = 15, count_diff_th: int = 500):
        self.diff_th = int(diff_th)                 # práh rozdílu jasu (0–255) pro 1 pixel
        self.count_diff_th = int(count_diff_th)     # kolik pixelů musí přesáhnout práh
        self.prev = None                            # předchozí grayscale snímek (referenční)

    def reset(self):
        self.prev = None                            # zapomenu referenci (po start/stop kamery)

    def update(self, gray_u8: np.ndarray) -> bool:
        if gray_u8.ndim != 2:                       # 2D grayscale
            raise ValueError("SimpleBackgroundDetector.update očekává 2D grayscale pole")

        if self.prev is None:                       # první snímek pouze uložím jako referenci
            self.prev = gray_u8.copy()
            return False                            # první snímek nehlásí dynamiku

        diff = cv2.absdiff(gray_u8, self.prev)                      # aktuální - předchozí
        changed_count = int(np.count_nonzero(diff > self.diff_th))  # počet „změněných“ pixelů
        self.prev = gray_u8.copy()                                  # posun reference na aktuální snímek
        return changed_count > self.count_diff_th                   # True = dynamický snímek


class CameraThread(threading.Thread):
    def __init__(self, name: str, baseLog: str, config):
        super().__init__(name=name)                  

        self.camPath = os.path.join(baseLog, 'CameraLog')   # složka pro JPEG výstupy
        os.makedirs(self.camPath, exist_ok=True)          

        # Parametry kamery z INI
        self.fps    = max(1,   config.getint('Camera', 'fps'))   
        self.exp_us = max(1,   config.getint('Camera', 'exp'))   
        self.iso    = max(100, config.getint('Camera', 'iso'))   
        self.ROI: Tuple[int,int,int,int] = (                     # výřez obrazu (l,t,r,b)
            int(config.getfloat('Camera', 'left')),
            int(config.getfloat('Camera', 'top')),
            int(config.getfloat('Camera', 'right')),
            int(config.getfloat('Camera', 'bottom')),
        )
        self.log_dec = max(1, config.getint('Camera', 'log_dec')) # každý N-tý dynamický snímek
        self._counter = 0                                 # čítač pro decimaci logování
        self._running = False                             # běží/neběží Picamera2
        self._period  = 1.0 / float(self.fps)             # perioda mezi snímky (s)

        # Detektor: porovnání s předchozím snímkem
        self._bg = SimpleBackgroundDetector(diff_th=15, count_diff_th=500)

# Picamera2 konfigurace
        self.picam2 = Picamera2()                         # Instance kamery
        self._size = (1280, 720)                          # Rozlišení kamery
        cfg = self.picam2.create_video_configuration(     # video konfigurace výstupu
            main={"size": self._size, "format": "RGB888"} # RGB888 --> gray
        )
        self.picam2.configure(cfg)                        # Načtení konfigurace

        analogue_gain = float(self.iso) / 100.0           # přepočet ISO → AnalogGain
        try:
            self.picam2.set_controls({                    
                "AeEnable": False,                        
                "AwbEnable": False,                       
                "ExposureTime": int(self.exp_us),         
                "AnalogueGain": max(1.0, analogue_gain),  
            })
        except Exception as e:
            logging.warning(f": Picamera2.set_controls error ({e})")

        eventCameraThread_run.set()                       # spustění vlákna
        def request_stop(self):
            eventCameraThread_run.clear()                 # vypne hlavní smyčku v run()

# ROI
    def _clamp_roi(self, w: int, h: int) -> Tuple[int,int,int,int]:
        l,t,r,b = self.ROI                                 
        l = max(0, min(l, w-1))                           
        r = max(l+1, min(r, w))                            
        t = max(0, min(t, h-1)) 
        b = max(t+1, min(b, h))                           
        return l,t,r,b                                     

# hlavní smyčka vlákna
    def run(self):
        last_tick = time.monotonic()                      # čas pro FPS
        while eventCameraThread_run.is_set():             # Dokud je vlákno povoleno
            if eventCamera_capture.is_set():              # Smímání je povoleno
                if not self._running:                     # Pokud kamera neběží:
                    try:
                        self.picam2.start()
                        self._running = True              
                        self._bg.reset()                  # reset detektoru
                        logging.info(": Picamera2 started")
                    except Exception as e:
                        logging.error(f": Picamera2: not started. error: {e}") 
                        time.sleep(0.5)                
                        continue
                try:
                    frame_rgb = self.picam2.capture_array("main")  # 1 snímek RGB888
                except Exception as e:
                    logging.error(f": capture_array error: {e}")  
                    time.sleep(self._period)                        # počkej do další periody
                    continue

                # ROI & grayscale
                h, w, _ = frame_rgb.shape               # velikost celého snímku
                l,t,r,b = self._clamp_roi(w, h)         # zajisti platné ROI
                roi_rgb  = frame_rgb[t:b, l:r]          # vyřízni barevné ROI
                gray     = cv2.cvtColor(roi_rgb, cv2.COLOR_RGB2GRAY)  # převod na grayscale (pro detektor)

                # Detekce změny a decimace ukládání
                if self._bg.update(gray):               # True = dynamický snímek
                    self._counter += 1                  
                    if self._counter >= self.log_dec:   # každý N-tý snímek
                        self._counter = 0               # reset čítače

                        filename = os.path.join(self.camPath, datetime.datetime.now().strftime("%y%m%d_%H%M%S%f") + ".jpeg") #Jméno souboru
                        try:
                            roi_bgr = cv2.cvtColor(roi_rgb, cv2.COLOR_RGB2BGR)          # převod pro imwrite
                            cv2.imwrite(filename, roi_bgr)                              # zápis na disk
                            logging.debug(f": Picture saved: {filename}")             
                        except Exception as e:
                            logging.error(f": Picture not saved. error: {e}")  

                # FPS controling
                now = time.monotonic()                                  # aktuální čas
                sleep_t = max(0.0, self._period - (now - last_tick))    # kolik zbývá do periody
                if sleep_t > 0:
                    time.sleep(sleep_t)                                 # sleep po dobu než je splněna perioda
                last_tick = time.monotonic()                            # nová reference pro další kolo

# Smímání je Zakázáno
            else:                                      
                if self._running:                      
                    try:
                        self.picam2.stop()              
                    except Exception as e:
                        logging.warning(f": Picamera2.stop error: {e}")  
                    self._running = False               # Kamera nastavena na False
                    self._bg.reset()                    # reset detektoru
                    logging.debug(": Picamera2 stop snímání.")
                time.sleep(0.1)                         

# Ukončení vlákna
        if self._running:                          
            try:
                self.picam2.stop()              
            except Exception as e:
                logging.warning(f": Picamera2.stop error: {e}")
        try:
            self.picam2.close()                       
        except Exception as e:
            logging.warning(f": Picamera2.close error: {e}")    
        logging.info(": CameraThread ended.")       
