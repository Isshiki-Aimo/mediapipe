import math
import time
from ctypes import cast, POINTER

import autopy
import cv2
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import HandTrackingModule as htm
from utils.util import compute_distance

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volumeRange = volume.GetVolumeRange()  # (-63.5, 0.0, 0.03125)
minVol = volumeRange[0]
maxVol = volumeRange[1]
##############################
wCam, hCam = 1280, 720
pt1, pt2 = (100, 100), (1100, 500)  # 虚拟鼠标的移动范围，左上坐标pt1，右下坐标pt2
frameR = 100
smoothening = 5
##############################
cap = cv2.VideoCapture(0)  # 若使用笔记本自带摄像头则编号为0  若使用外接摄像头 则更改为1或其他编号
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

stable_thres = 40  # 判断为稳定触发的时间
stop_thres = 15  # 判断为停滞的移动距离
stop_time = [0, 0]
stop_time1 = [-50]
old_lmList = None
functionflag1 = False
detector = htm.handDetector()
wScr, hScr = autopy.screen.size()
print(wScr, hScr)


def voiceControl(img, lmList, old_lmList, functionflag1):
    draw = True
    functionflag = False
    if len(lmList):
        # 下面实现长度到音量的转换
        # 判断食指是否稳定
        stop_length = compute_distance(lmList[8][1], lmList[8][2], old_lmList[8][1], old_lmList[8][2])
        fingers = detector.fingersUp()

        if fingers[0] and fingers[1]:
            functionflag = True
            if stop_length < stop_thres or functionflag1:
                if stop_time[1] < stable_thres:
                    stop_time[1] += 1
                fill_cnt = stop_time[1] / stable_thres * 360
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
                if 0 < fill_cnt < 360:
                    cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    draw = True
                    # 进入功能调节音量
                else:
                    if draw:
                        cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (0, 150, 255),
                                    4)
                        functionflag1 = True
                        old_lmList = lmList
                        x1, y1, x2, y2 = lmList[4][1], lmList[4][2], lmList[8][1], lmList[8][2]
                        xc, yc = (x2 + x1) // 2, (y2 + y1) // 2
                        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (xc, yc), 15, (255, 0, 255), cv2.FILLED)
                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                        length = math.hypot(x2 - x1, y2 - y1)  # 15--200
                        if length < 25:
                            cv2.circle(img, (xc, yc), 15, (0, 255, 0), cv2.FILLED)

                        # 下面实现长度到音量的转换
                        # np.interp为插值函数，简而言之，看line_len的值在[15，200]中所占比例，然后去[min_volume,max_volume]中线性寻找相应的值，作为返回值
                        vol = np.interp(length, [15, 200], [minVol, maxVol])
                        # 用之前得到的vol值设置电脑音量
                        volume.SetMasterVolumeLevel(vol, None)
                        volBar = np.interp(length, [15, 200], [350, 150])
                        volPer = np.interp(length, [15, 200], [0, 100])

                        cv2.rectangle(img, (20, 150), (50, 350), (255, 0, 255), 2)
                        cv2.rectangle(img, (20, int(volBar)), (50, 350), (255, 0, 255), cv2.FILLED)
                        cv2.putText(img, f'{int(volPer)}%', (10, 380), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)

                    if stop_length < stop_thres - 5:
                        if stop_time1[0] < stable_thres:
                            stop_time1[0] += 1
                        fill_cnt = stop_time1[0] / stable_thres * 360
                        cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
                        if 0 < fill_cnt < 360:
                            cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (0, 255, 0),
                                        2)
                        if fill_cnt == 360:
                            draw = False
                            stop_time1[0] = -50
                            stop_time[1] = -50
                            functionflag1 = False
                            functionflag = True
                    else:
                        stop_time1[0] = 0

            else:
                stop_time[1] = 0

        else:
            stop_time[1] = 0

        old_lmList = lmList
    return img, functionflag, old_lmList, functionflag1


while True:
    success, img = cap.read()
    # 1. 检测手部 得到手指关键点坐标
    img = detector.findHands(img)
    cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (0, 255, 0), 2, cv2.FONT_HERSHEY_PLAIN)
    lmList = detector.findPosition(img)

    if old_lmList is None and len(lmList):
        old_lmList = lmList

    img, functionflag, old_lmList, functionflag1 = voiceControl(img, lmList, old_lmList, functionflag1)

    # 2. 判断食指和中指是否伸出
    if len(lmList) != 0 and functionflag == False:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        fingers = detector.fingersUp()

        # 3. 若只有食指伸出 则进入移动模式
        if fingers[1] and fingers[2] == False:
            # 4. 坐标转换： 将食指在窗口坐标转换为鼠标在桌面的坐标
            # 鼠标坐标
            # x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            # y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

            x3 = np.interp(x1, (pt1[0], pt2[0]), (0, wScr))
            y3 = np.interp(y1, (pt1[1], pt2[1]), (0, hScr))

            # smoothening values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            # autopy.mouse.move(x3, y3)  # 给出鼠标移动位置坐标

            autopy.mouse.move(clocX, clocY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # 5. 若是食指和中指都伸出 则检测指头距离 距离够短则对应鼠标点击
        if fingers[1] and fingers[2]:
            length, img, pointInfo = detector.findDistance(8, 12, img)
            if length < 60:

                if stop_time[0] < stable_thres:
                    stop_time[0] += 1

                fill_cnt = stop_time[0] / stable_thres * 360
                cv2.circle(img, ((pointInfo[4], pointInfo[5])), 15, (0, 255, 0), cv2.FILLED)
                if 0 < fill_cnt < 360:
                    cv2.ellipse(img, ((pointInfo[4], pointInfo[5])), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    # 进入功能开始调节音量
                else:
                    stop_time[0] = 0
                    autopy.mouse.click()
            else:
                stop_time[0] = 0

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'fps:{int(fps)}', [15, 25],
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
