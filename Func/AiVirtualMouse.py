import time

import autopy
import cv2
import numpy as np

import HandTrackingModule as htm

##############################
wCam, hCam = 1080, 720
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
stop_time = [0]

detector = htm.handDetector()
wScr, hScr = autopy.screen.size()
# print(wScr, hScr)

while True:
    success, img = cap.read()
    # 1. 检测手部 得到手指关键点坐标
    img = detector.findHands(img)
    cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (0, 255, 0), 2, cv2.FONT_HERSHEY_PLAIN)
    lmList = detector.findPosition(img)

    # 2. 判断食指和中指是否伸出
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        fingers = detector.fingersUp()

        # 3. 若只有食指伸出 则进入移动模式
        if fingers[1] and fingers[2] == False:
            # 4. 坐标转换： 将食指在窗口坐标转换为鼠标在桌面的坐标
            # 鼠标坐标
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

            # smoothening values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            autopy.mouse.move(wScr - clocX, clocY)
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
