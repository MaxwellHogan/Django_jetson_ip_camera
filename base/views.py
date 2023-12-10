from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading

class VideoCamera(object):
    def __init__(self, gstreamer_config, post_process = None):
        self.post_process = post_process
        self.cap = cv2.VideoCapture(gstreamer_config)
        
        ret, frame = self.cap.read()
        # print(ret)
        if not ret:
            self.frame = cv2.imread("no_signal.jpg")
            # print("HERE",self.frame)
        else:
            self.frame = frame
            # print(self.frame)

        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.cap.release()

    def get_frame(self):
        frame = self.frame
        
        return frame

    def update(self):
        while True:
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
    frame = cv2.flip(frame, 0) ## I mounted my cams upside down
    return frame

gstreamer_config0 = "nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)640, height=(int)480,format=(string)NV12, framerate=(fraction)10/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink"
cam0 = VideoCamera(gstreamer_config0, post_process=post_process_example)
@gzip.gzip_page
def cam0_stream(request):
    return StreamingHttpResponse(gen(cam0), content_type="multipart/x-mixed-replace;boundary=frame")

gstreamer_config1 = "nvarguscamerasrc sensor-id=1 ! video/x-raw(memory:NVMM), width=(int)640, height=(int)480,format=(string)NV12, framerate=(fraction)10/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink"
cam1 = VideoCamera(gstreamer_config1, post_process=post_process_example)
@gzip.gzip_page
def cam1_stream(request):
    return StreamingHttpResponse(gen(cam1), content_type="multipart/x-mixed-replace;boundary=frame")
############################# END SET UP STREAMING OBJECTS #############################

def stream_page(request):
    context = {}
    return render(request, "base/stream_page.html", context)