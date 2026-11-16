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

    @staticmethod
    def highlightLeftInvalidBand(colored, disparity):
        """Tint the contiguous invalid strip at the map's left edge."""
        valid_fraction = np.mean(disparity > 0, axis=0)
        valid_columns = np.flatnonzero(valid_fraction > 0.5)
        if valid_columns.size == 0:
            return colored

        band_width = int(valid_columns[0])
        if band_width == 0:
            return colored

        highlighted = colored.copy()
        invalid = disparity[:, :band_width] <= 0
        band = highlighted[:, :band_width]
        band[invalid] = (0, 0, 128)
        if band_width < highlighted.shape[1]:
            cv2.line(highlighted, (band_width, 0), (band_width, highlighted.shape[0] - 1), (0, 0, 255), 1)
        return highlighted