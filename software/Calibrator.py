import numpy as np
import cv2 as cv
       
class Calibrator(object):
    def __init__(self):
        self.fx = 28511
        self.fy = 29826
        self.cx = 634.6212
        self.cy = 362.5117

        self.k1 = -248.572842168091
        self.k2 = 63489.7810239253

        self.mtx = np.zeros((3,3))
        self.mtx[0,0] = self.fx
        self.mtx[1,1] = self.fy
        self.mtx[0,2] = self.cx
        self.mtx[1,2] = self.cy
        self.mtx[2,2] = 1

        self.dist = np.zeros(4)
        self.dist[0] = self.k1
        self.dist[1] = self.k2
    
    def Calib(self, OrigImg):
        h,  w = OrigImg.shape[:2]
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(self.mtx, self.dist, (w,h), 1, (w,h))
        dst = cv.undistort(OrigImg, self.mtx, self.dist, None, newcameramtx)
        
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]#crop of image from calibration
        crop = dst[164:464,49:1165]#crop image to see only tunnels with bees
        return crop