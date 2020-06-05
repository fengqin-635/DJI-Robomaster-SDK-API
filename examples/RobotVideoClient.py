import threading
import signal
import opus_decoder
import pyaudio
import os
import sys
from PIL import Image as PImage
import cv2
import numpy as np
import queue
import time
import signal
from rm import Robomaster

class RobotVideoClient:

    def __init__(self,robot):
        self.rm = robot
        self.frame = None
        self.videothread = threading.Thread(target=self.videoLoop, args=())
        self.audiothread = threading.Thread(target=self.audioLoop, args=())
        self.stopEvent = True
        self.rmReady = False
        self.runRMthread = threading.Thread(target=self.rmLoop, args=())
        self.stopApp = False

    def rmLoop(self):
# loop to control action of robomaster. put your robotmaster code here in this rmloop function

        if self.rm.start_sdk_session('192.168.2.1') == 1:
            self.rmReady = True
            self.stopEvent = False
            if self.rm.video_on() == True:
                self.videothread.start()
                if self.rm.audio_on() == True:
                    self.audiothread.start()
                else:
                    print('no audio')
            else:
                print('no video')

# put your robomaster code starting from here
        if self.rmReady:
            self.rm.instruct('chassis move x 2 y 2')
            self.rm.instruct('chassis move z 90')
            self.rm.instruct('chassis move x -2 y -2')
            i = 0
            while i < 5:
                time.sleep(1)
                i = i + 1
            self.rm.instruct('chassis move z 180')
            self.rm.instruct('chassis move z 180')
            i = 0
            while i < 10:
                time.sleep(1)
                i = i + 1
            self.rm.instruct('chassis move x 1 y 2')
            while i < 10:
                time.sleep(1)
                i = i + 1
# put your robomaster code ends here
        self.stopEvent = True

    def start(self):
#        self.runTellothread.start()
        self.runRMthread.start()
 
    def videoLoop(self):

        while self.stopEvent == False:
            if self.rmReady:
                vframe = self.rm.getvideoframe()
            
            if vframe is None:
                continue

            cv2.namedWindow("RMLiveview")
            rimage = PImage.fromarray(vframe)            
            rimg = cv2.cvtColor(np.array(rimage), cv2.COLOR_RGB2BGR)
            cv2.imshow("RMLiveview", rimg)
            k = cv2.waitKey(1)

            if 'q' == chr(k & 255):
                self.stopEvent = True

        self.onClose()

    def audioLoop(self):
        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paInt16,channels=1,rate=48000,output=True)

        while self.stopEvent == False:
            a_output = self.rm.getaudioframe()

            if a_output:
                stream.write(a_output)
            else:
                print("audio stream empty")

        stream.stop_stream()
        stream.close()

    def onClose(self):
        print("Close window")
        self.stopEvent = True
        time.sleep(0.5)
        self.rm.close()
    

if __name__ == '__main__':
    try:

        r = Robomaster()
        av = RobotVideoClient(r)
        av.start()

    except KeyboardInterrupt:
        sys.exit(0)

