import numpy as np
import cv2


class BackgroundModel:
    """Background subtraction adaptive model
    """
    def __init__(self, diff_th, count_diff_th, model_diff_th, model_count_diff_th, alpha=0.01, background_init_frame=None):
        """
        Args:
            diff_th (int): difference threshold to classify scene as dynamic or static
            count_diff_th (int): number of dynamic pixels required to classify as dynamic
            model_diff_th (int): difference threshold to classify frame as dynamic with respect to model
            model_count_diff_th (int): number of dynamic pixels required to classify scene as dynamic with respect to model
            alpha (float, optional): model learning rate. Defaults to 0.01.
            background_init_frame (numpy.ndarray, optional): dynamic model initial frame. Defaults to None.
        """
        self.diff_th = diff_th
        self.count_diff_th = count_diff_th
        self.model_diff_th = model_diff_th
        self.model_count_diff_th = model_count_diff_th
        self.alpha = alpha

        self.prev = background_init_frame
        self.model = background_init_frame

    def update(self, img):
        """Update dynamic model, first frame is set as the initial model

        Args:
            img (numpy.ndarray): monochromatic frame
        """
        img = cv2.medianBlur(img, 7)
        # if this is the first frame, set it as model
        if self.prev is None or self.model is None:
            self.prev, self.model = img, img
            return
        # check if sccene is dynamic with respect to prev frame, if static -> continue
        dynamic_scene = self.is_dynamic(img, self.prev, self.diff_th, self.count_diff_th)
        if not dynamic_scene:
            # check if scene is dynamic with respect to model, update model if static
            dynamic_model = self.is_dynamic(img, self.model, self.model_diff_th, self.model_count_diff_th)
            if not dynamic_model:
                self.model = self.alpha * img.astype(np.float32) + (1 - self.alpha) * self.model
        self.prev = img
    
    def get_mask(self, img):
        """Motion mask, frame to model

        Args:
            img (np.ndarray): monochromatic frame

        Returns:
            numpy.ndarray: boolean mask
        """
        # two-way thresholded subtraction, morph open to clear noise
        mask = np.abs(img.astype(np.float32) - self.model.astype(np.float32)) > self.model_diff_th
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7))).astype(bool)
        return mask

    @staticmethod
    def is_dynamic(img1, img2, diff_th, count_th):
        """Classify scene as dynamic or static from two frames

        Args:
            img1 (numpy.ndarray): monochromatic frame
            img2 (numnpy.ndarray): monochromatic frame
            diff_th (int): difference threshold to classify scene as dynamic or static
            count_th (int): number of dynamic pixels required to classify as dynamic

        Returns:
            bool: True if dynamic, False otherwise
        """
        # two-way thresholded subtraction, if number of positive elements is greate then threhsold, scene is dynamic
        diff = np.abs(img1.astype(np.float32) - img2.astype(np.float32))
        return np.count_nonzero(diff > diff_th) > count_th
