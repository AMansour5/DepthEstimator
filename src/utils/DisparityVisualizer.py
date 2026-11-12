import cv2 
import numpy as np 

class DisparityVisualizer:

    @staticmethod
    def drawText(img, text, org, scale=0.5):
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3)
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1)

    @staticmethod
    def colorizeDisparity(disparity, num_disparities):
        valid = disparity > 0
        vis = np.zeros(disparity.shape, dtype=np.uint8)
        if np.any(valid):
            vis[valid] = np.clip(disparity[valid] * 255.0 / num_disparities, 0, 255).astype(np.uint8)
        colored = cv2.applyColorMap(vis, cv2.COLORMAP_TURBO)
        colored[~valid] = (0, 0, 0)
        return colored