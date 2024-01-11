from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import *
# from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading
import numpy as np

class VideoCamera:
    def __init__(self, gstreamer_config, post_process = None, enable = True):
        self.post_process = post_process

        if enable:
            self.cap = cv2.VideoCapture(gstreamer_config)
            ret, frame = self.cap.read()
        else:
            ret = False

        self.enable = enable

        if not ret:
            self.frame = cv2.resize(cv2.imread("no_signal.jpg"), (640, 480))
            # print("HERE",self.frame)
        else:
            self.frame = frame

        self.thread = threading.Thread(target=self.update, args=())
        self.live = False
        # self.start() ## start thread

    def __del__(self):
        self.stop()
        self.cap.release()

    def get_frame(self):
        frame = self.frame
        return frame
    
    def start(self):
        if not self.live and self.enable:
            self.live = True
            self.thread.start()

    def stop(self):
        if self.live:
            self.live = False
            self.thread.join() ## make sure the frame shuts down 
            self.frame = cv2.resize(cv2.imread("no_signal.jpg"), (720, 640)) ## put in placeholder 

    def update(self):
        while True:
            if not self.live:
                break
            ret, frame = self.cap.read()
            if ret:
                if self.post_process: frame = self.post_process(frame)
                self.frame = frame

def gen(camera):
    while True:
        frame = camera.get_frame()
        return_key, encoded_image = cv2.imencode(".jpg", frame)

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encoded_image) + b'\r\n')

############################ BEGIN SET UP STREAMING OBJECTS ############################
def post_process_example(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
    # frame = cv2.flip(frame, 0) ## I mounted my cams upside down
    return frame


class Detect_circle:
    def __init__(self):
        
        dilatation_size = 6
        dilation_shape = cv2.MORPH_ELLIPSE
        self.element = cv2.getStructuringElement(dilation_shape, (2 * dilatation_size + 1, 2 * dilatation_size + 1),
                                                (dilatation_size, dilatation_size))
        
        # Setup SimpleBlobDetector parameters.
        params = cv2.SimpleBlobDetector_Params()
        
        # Change thresholds
        params.filterByColor = False
        
        # Filter by Area.
        params.filterByArea = True
        params.minArea = int(np.pi*(50/2)**2)
        params.maxArea = int(np.pi*(500/2)**2)
        
        # Filter by Circularity
        params.filterByCircularity = False
        params.minCircularity = 0.1
        
        # Filter by Convexity
        params.filterByConvexity = False
        params.minConvexity = 0.87
        
        # Filter by Inertia
        params.filterByInertia = False
        params.minInertiaRatio = 0.01

        # Set up the detector with default parameters.
        self.detector = cv2.SimpleBlobDetector_create(params)
        self.first = True

        ## set the target cicle we will be matching 
        self.target_xy = (311, 186)
        self.target_r = 142

        self.target = np.zeros((720, 640), dtype = np.uint8)
        self.target = cv2.circle(self.target, self.target_xy, self.target_r, 1, -1)


    def __call__(self,frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
        mask = ((frame[:,:,0] < 100) & (frame[:,:,1] < 100) & (frame[:,:,2] < 100)).astype(np.uint8)*255
        mask = cv2.dilate(mask, kernel = self.element)

        cIoU = 0
        # frame[mask] = (255,255,255)
        # frame = cv2.flip(frame, 0) ## I mounted my cams upside down

        # Detect blobs.
        keypoints = self.detector.detect(mask)
        if len(keypoints) != 0: 
            x = int(keypoints[0].pt[0])
            y = int(keypoints[0].pt[1])
            r = int(keypoints[0].size/2)

            frame = cv2.circle(frame, (x,y), r, (0,0,255), 2)

            pred = np.zeros((720, 640), dtype = np.uint8)
            pred = cv2.circle(pred, (x,y), r, 1, -1)

            intersect = (self.target*pred).sum()
            union = np.logical_or(self.target, pred).sum()

            cIoU = intersect/union

        frame = cv2.circle(frame, self.target_xy, self.target_r, (0,255,0), 2)
        frame = cv2.putText(frame, "%.2f" %cIoU, (100,100), cv2.FONT_HERSHEY_SIMPLEX, 3, (255,0,0), 1, cv2.LINE_AA)
        
        return frame


cam0 = None

@gzip.gzip_page
def cam0_stream(request):
    return StreamingHttpResponse(gen(cam0), content_type="multipart/x-mixed-replace;boundary=frame")

## place holder 
cam1 = None 

@gzip.gzip_page
def cam1_stream(request):
    return StreamingHttpResponse(gen(cam1), content_type="multipart/x-mixed-replace;boundary=frame")
############################# END SET UP STREAMING OBJECTS #############################

def stream_page(request):
    context = {}
    
    if cam0 is None:
        print("Setting up camera 0")
        gstreamer_config0 = "nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)640, height=(int)480,format=(string)NV12, framerate=(fraction)28/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink"
        globals()["cam0"] = VideoCamera(gstreamer_config0, post_process=post_process_example)
    if cam1 is None:
        print("Setting up camera 1")
        gstreamer_config1 = "nvarguscamerasrc sensor-id=1 ! video/x-raw(memory:NVMM), width=(int)640, height=(int)480,format=(string)NV12, framerate=(fraction)28/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink"
        globals()["cam1"] = VideoCamera(gstreamer_config1, post_process=Detect_circle(), enable = True)

    if not cam0.live:
        cam0.start()
    if not cam1.live:
        cam1.start()

    return render(request, "base/stream_page.html", context)
