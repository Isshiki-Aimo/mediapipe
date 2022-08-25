import time
from pykeyboard import PyKeyboard
import autopy
import cv2
import HandTrackingModule as htm
from utils.findWindow import *

wCam, hCam = 704, 480
frameR = 100
smoothing = 5
pTime = 0
flag = 0
constantId = 0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

plocX3, plocY3 = 0, 0
clocX3, clocY3 = 0, 0

stable_thres = 40  # 判断为稳定触发的时间
stop_time = [0]

detector = htm.handDetector()
wScr, hScr = autopy.screen.size()

while True:
    k = PyKeyboard()

    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img)

    if len(lmList) != 0:
        x1, y1 = lmList[4][1:]
        x2, y2 = lmList[8][1:]
        x3, y3 = lmList[12][1:]
        x4, y4 = lmList[16][1:]
        x5, y5 = lmList[20][1:]
        fingers = detector.fingersUp()

        # #功能1：切换上一个视频
        # cv2.circle(img, (x3, y3), 15, (255, 0, 255), cv2.FILLED)
        # clocY3 = y3
        # if clocY3 - plocY3 > 50:
        #     failampHandle = findWindow('Failamp')
        #     changeWindow(failampHandle)
        #     k.press_keys([k.alt_key, 'p'])
        #     k.release_key(k.alt_key)
        #     k.release_key('p')
        #     print("previous video")
        # plocY3 = clocY3
        #
        #
        # #功能2:切换下一个视频
        # cv2.circle(img, (x3, y3), 15, (255, 0, 255), cv2.FILLED)
        # clocY3 = y3
        # if plocY3 - clocY3 > 50:
        #     failampHandle = findWindow('Failamp')
        #     changeWindow(failampHandle)
        #     k.press_keys([k.alt_key, 'n'])
        #     k.release_key(k.alt_key)
        #     k.release_key('n')
        #     print("next video")
        # plocY3 = clocY3

        #功能3：暂停， 利用4, 7关节距离较小时触发
        x7, y7 = lmList[7][1:]
        length, img, pointInfo = detector.findDistance(4, 7, img, draw=False)
        if length < 50:
            if stop_time[0] < stable_thres:
                stop_time[0] += 1

            fill_cnt = stop_time[0] / stable_thres * 360
            cv2.circle(img, ((pointInfo[4], pointInfo[5])), 15, (0, 255, 0), cv2.FILLED)
            if 0 < fill_cnt < 360:
                pass
            # 进入暂停功能
            else:
                stop_time[0] = 0

                if flag == 0:
                    failampHandle = findWindow('Failamp')
                    constantId = failampHandle
                    flag += 1
                else:
                    failampHandle = findWindow('Failamp')

                print('FailampID:', failampHandle)
                print('constantId', constantId)
                changeWindow(constantId)
                k.press_key(k.control_key)
                k.tap_key(k.space_key)
                print("video paused")
                k.release_key(k.control_key)
        else:
            pass

        # #功能4：播放，五指同时伸出后保持触发
        if all(fingers):
            if stop_time[0] < stable_thres:
                stop_time[0] += 1
            print(stop_time[0])
            fill_cnt = stop_time[0] / stable_thres * 360
            cv2.circle(img, (x3, y3), 15, (0, 255, 0), cv2.FILLED)
            if 0 < fill_cnt < 360:
                cv2.ellipse(img, (x3, y3), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                            2)
            #进入播放功能
            else:
                if flag == 0:
                    failampHandle = findWindow('Failamp')
                    constantId = failampHandle
                    flag += 1
                else:
                    failampHandle = findWindow('Failamp')
                stop_time[0] = 0
                changeWindow(constantId)
                k.tap_key(k.space_key)
                print("video palyed")
        else:
            pass

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'fps: {int(fps)}', (10, 40), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.imshow("Image", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
