# Depth Estimator
The aim of this project is to use YOLO object detection and estimate the depth of each detected object in the frame using stereo camera.
## Objectives

- [ ] Reuse camera class and get both frames of the stereo camera 
- [ ] Write depth estimation equations in a class 
- [ ] Build a module around yolo that takes frames and returns then annotated with the object detect in them 

### DepthEstimation module
- The class takes two annotated images as input.
- Performs depth equations and rectification on the images. 
- Returns single annotated frame with depth of an object 

### ObjectDetection module 
- The class takes two raw frames from the camera
- Performs object detection on them. 
- return two annotated frames with objects detected in them. 