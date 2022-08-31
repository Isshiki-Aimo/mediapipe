import time
from ctypes import cast, POINTER
import cv2
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pykeyboard import PyKeyboard
import HandTrackingModule as htm
from utils.util import compute_distance, compute_direction
from utils.findWindow import findWindow, changeWindow
import math
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volumeRange = volume.GetVolumeRange()  # (-63.5, 0.0, 0.03125)
minVol = volumeRange[0]
maxVol = volumeRange[1]

#############################
wCam, hCam = 1080, 720
#############################
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
detector = htm.handDetector()
stop_thres = 15  # 判断为停滞的移动距离
stable_thres = 20  # 判断为稳定触发的时间
global stop_time
stop_time = [0, 0, 0, 0,0,0]  # 停滞时间记录
intervalTime = [0, 0, 0, 0]  # 间隔时间记录
stop_time1 = [-50]
old_lmList = None
global draw
draw = True
moveCount = 50
failampHandle = findWindow('Failamp')
k = PyKeyboard()

def func_play(img, fingers, lmList, failampHandle):
    # 功能1: 播放功能，五指伸出保持静止后触发
    if all(fingers):
        stop_length = compute_distance(lmList[8][1], lmList[8][2], old_lmList[8][1], old_lmList[8][2])
        if stop_length < stop_thres:
            if stop_time[0] < stable_thres:
                stop_time[0] += 1
            fill_cnt = stop_time[0] / stable_thres * 360
            cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
            if 0 < fill_cnt < 360:
                cv2.ellipse(img, (lmList[12][1], lmList[12][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                            2)

            else:
                # 进入播放功能
                stop_time[0] = 0
                changeWindow(failampHandle)
                k.tap_key(k.space_key)
                print("video palyed")

        else:
            stop_time[0] = 0
    else:
        stop_time[0] = 0


def func_pause(img, lmList,failampHandle):
    #  功能2：暂停功能，五指收起保持静止后触发
    length, img, pointInfo = detector.findDistance(4, 7, img, draw=False)
    if length < 50:

        stop_length = compute_distance(lmList[4][1], lmList[4][2], old_lmList[4][1], old_lmList[4][2])
        if stop_length < stop_thres:
            if stop_time[1] < stable_thres:
                stop_time[1] += 1

            fill_cnt = stop_time[1] / stable_thres * 360
            cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
            if 0 < fill_cnt < 360:
                cv2.ellipse(img, (lmList[4][1], lmList[4][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                            2)

            else:
                # 进入暂停功能
                stop_time[1] = 0
                changeWindow(failampHandle)
                k.press_key(k.control_key)
                k.tap_key(k.space_key)
                k.release_key(k.control_key)
                print("video paused")
        else:
            stop_time[1] = 0
    else:
        stop_time[1] = 0


def func_previous(img, fingers, lmList,failampHandle):
    # 功能3：切换上一个，五指下滑，触发间隔3秒
    global moveCount
    if all(fingers) and time.time() - intervalTime[2] > 3:
        direction = compute_direction(lmList[12][1], lmList[12][2], old_lmList[12][1], old_lmList[12][2])
        if direction == 2:
            moveCount += 5
        cv2.circle(img, (lmList[4][1], lmList[4][2]), 15, (255, 0, 255), cv2.FILLED)
        if moveCount > 75:
            changeWindow(failampHandle)
            k.press_key(k.alt_key)
            k.tap_key('p')
            k.release_key(k.alt_key)
            print("previous video")
            moveCount = 50
            intervalTime[2] = time.time()
    else:
        moveCount = 50


def func_next(img, fingers, lmList, failampHandle):
    # 功能4：切换下一个，五指上划，触发间隔3秒
    global moveCount
    if all(fingers) and time.time() - intervalTime[3] > 3:
        direction = compute_direction(lmList[12][1], lmList[12][2], old_lmList[12][1], old_lmList[12][2])
        if direction == 8:
            moveCount -= 5
        cv2.circle(img, (lmList[4][1], lmList[4][2]), 15, (255, 0, 255), cv2.FILLED)
        if moveCount < 25:
            changeWindow(failampHandle)
            k.press_key(k.alt_key)
            k.tap_key('n')
            k.release_key(k.alt_key)
            print("next video")
            moveCount = 50
            intervalTime[3] = time.time()
    else:
        moveCount = 50


def func_scale(img,lmList,old_lmList,failampHandle,window,fingers):
    # 功能5：双手缩放视频
    if len(lmList)>21:
        if lmList[8][2] < lmList[8 - 2][2] and lmList[29][2] < lmList[29 - 2][2] and  lmList[12][2] < lmList[12 - 2][2] and lmList[33][2] < lmList[33 - 2][2]:
            stop_length = compute_distance(lmList[8][1], lmList[8][2], old_lmList[8][1], old_lmList[8][2])
            if stop_length < stop_thres  :
                if stop_time[5] < stable_thres:
                    stop_time[5] += 1
                fill_cnt = stop_time[5] / stable_thres * 360
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lmList[29][1], lmList[29][2]), 15, (0, 255, 0), cv2.FILLED)
                if 0 < fill_cnt < 360:
                    cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    cv2.ellipse(img, (lmList[29][1], lmList[29][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    global draw
                    draw = True
                    # 进入功能调节
                else:
                    if draw:
                        cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (0, 150, 255),
                                    4)
                        x1, y1, x2, y2 = lmList[8][1], lmList[8][2], lmList[29][1], lmList[29][2]
                        x3, y3, x4, y4 = lmList[12][1], lmList[12][2], lmList[33][1], lmList[33][2]
                        xc, yc = (x2 + x1) // 2, (y2 + y1) // 2
                        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (x3, y3), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (x4, y4), 15, (255, 0, 255), cv2.FILLED)
                        # cv2.circle(img, (xc, yc), 15, (255, 0, 255), cv2.FILLED)
                        x=abs(x1-x2)
                        y=abs(y1-y2)


                        window.viewer.setFixedSize(x,2*y)
        else:
            stop_time[5] = 0

    pass


def func_progress(img,lmList,old_lmList,failampHandle,window,fingers):
    if len(lmList)>21:
        if lmList[8][2] < lmList[8 - 2][2] and lmList[29][2] < lmList[29 - 2][2] and lmList[12][2] > lmList[12 - 2][2] and lmList[33][2] > lmList[33 - 2][2]:
            stop_length = compute_distance(lmList[8][1], lmList[8][2], old_lmList[8][1], old_lmList[8][2])
            if stop_length < stop_thres  :
                if stop_time[4] < stable_thres:
                    stop_time[4] += 1
                fill_cnt = stop_time[4] / stable_thres * 360
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 15, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lmList[29][1], lmList[29][2]), 15, (0, 255, 0), cv2.FILLED)
                if 0 < fill_cnt < 360:
                    cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    cv2.ellipse(img, (lmList[29][1], lmList[29][2]), (30, 30), 0, 0, fill_cnt, (255, 255, 0),
                                2)
                    global draw
                    draw = True
                    # 进入功能调节
                else:
                    if draw:
                        cv2.ellipse(img, (lmList[8][1], lmList[8][2]), (30, 30), 0, 0, fill_cnt, (0, 150, 255),
                                    4)
                        x1, y1, x2, y2 = lmList[8][1], lmList[8][2], lmList[29][1], lmList[29][2]
                        xc, yc = (x2 + x1) // 2, (y2 + y1) // 2
                        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
                        cv2.circle(img, (xc, yc), 15, (255, 0, 255), cv2.FILLED)
                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                        length = math.hypot(x2 - x1, y2 - y1)  # 15--200
                        position=length/1080.0*window.max
                        window.timeSlider.setValue(position)

        else:
            stop_time[4] = 0
            pass
    # 功能6： 双手食指控制进度
    pass


def func_voice():
    # 功能6： 单手拇指食指控制音量
    pass


def update(failampHandle,window):
    k = PyKeyboard()
    global old_lmList, pTime
    while True:
        ret, img = cap.read()
        img = detector.findHands(img)
        lmList = detector.findPosition(img)

        if old_lmList is None and len(lmList):
            print('old_lmList is None and len(lmList)')
            old_lmList = lmList

        if len(lmList) and len(old_lmList):
            fingers = detector.fingersUp()
            print(fingers[0])

            func_play(img, fingers, lmList, failampHandle)
            func_pause(img, lmList, failampHandle)
            func_previous(img, fingers, lmList, failampHandle)
            func_next(img, fingers, lmList, failampHandle)
            func_progress(img,lmList,old_lmList,failampHandle,window,fingers)
            func_scale(img, lmList, old_lmList, failampHandle, window,fingers)

        old_lmList = lmList

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'fps: {int(fps)}', (10, 40), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
