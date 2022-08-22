import time
from ctypes import cast, POINTER

import cv2
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import HandTrackingModule as htm
from angle_util import *
from util import *


class Voice_Change:
    def __init__(self, minVol, maxVol, stop_thres, stable_thres, stop_time, detector, cap, volume):
        self.pTime = 0
        self.minVol = minVol  # 系统音量最大值
        self.maxVol = maxVol  # 系统音量最小值
        self.stop_thres = stop_thres  # 判断为停滞的移动距离
        self.stable_thres = stable_thres  # 判断为稳定触发的时间
        self.stop_time = stop_time  # 记录停滞时间
        self.detector = detector  # 追踪器
        self.cap = cap
        self.lmList = None
        self.old_lmList = None
        self.functionflag = False
        self.movecount = 50
        self.volume = volume

    def update(self):
        ret, img = self.cap.read()
        img = self.detector.findHands(img)
        self.lmList = self.detector.findPosition(img)

        if self.old_lmList is None and len(self.lmList):
            self.old_lmList = self.lmList

        if len(self.lmList):
            stop_length = compute_distance(self.lmList[8][1], self.lmList[8][2], self.old_lmList[8][1],
                                           self.old_lmList[8][2])
            fingers = self.detector.fingersUp()
            if fingers[1] and fingers[2]:
                length, img, pointInfo = self.detector.findDistance(8, 12, img)
                if (length < 60 and stop_length < self.stop_thres) or self.functionflag:
                    if self.stop_time < self.stable_thres:
                        self.stop_time += 1
                    fill_cnt = self.stop_time / self.stable_thres * 360
                    cv2.circle(img, (self.lmList[8][1], self.lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
                    if 0 < fill_cnt < 360:
                        cv2.ellipse(img, (self.lmList[8][1], self.lmList[8][2]), (30, 30), 0, 0, fill_cnt,
                                    (255, 255, 0),
                                    2)
                    else:
                        cv2.ellipse(img, (self.lmList[8][1], self.lmList[8][2]), (30, 30), 0, 0, fill_cnt,
                                    (0, 150, 255),
                                    4)
                        self.functionflag = True
                        length, img, pointInfo = self.detector.findDistance(8, 12, img)
                        if length > 60:
                            self.stop_time = 0
                            self.functionflag = False

                        direction = compute_direction(self.lmList[8][1], self.lmList[8][2], self.old_lmList[8][1],
                                                      self.old_lmList[8][2])
                        if direction == 2:
                            self.movecount -= 3
                        elif direction == 8:
                            self.movecount += 3
                        vol = np.interp(self.movecount, [0, 100], [self.minVol, self.maxVol])
                        self.volume.SetMasterVolumeLevel(vol, None)
                        volBar = np.interp(self.movecount, [0, 100], [350, 150])
                        volPer = np.interp(self.movecount, [0, 100], [0, 100])
                        cv2.rectangle(img, (20, 150), (50, 350), (255, 0, 255), 2)
                        cv2.rectangle(img, (20, int(volBar)), (50, 350), (255, 0, 255), cv2.FILLED)
                        cv2.putText(img, f'{int(volPer)}%', (10, 380), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                else:
                    self.stop_time = 0
            else:
                self.stop_time = 0

            self.old_lmList = self.lmList

            cTime = time.time()
            fps = 1 / (cTime - self.pTime)
            pTime = cTime
            cv2.putText(img, f'fps: {int(fps)}', (10, 40), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

            return img

            # cv2.imshow("Image", img)


if __name__ == '__main__':
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volumeRange = volume.GetVolumeRange()
    minVol = volumeRange[0]
    maxVol = volumeRange[1]
    wCam, hCam = 1080, 720
    #############################
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)
    detector = htm.handDetector()

    v = Voice_Change(minVol, maxVol, 10, 30, 0, detector, cap, volume)

    while True:
        img = v.update()
        cv2.imshow("Image", img)
