import math
import time

import cv2
import mediapipe as mp

from utils import angle_util


class handDetector():
    # modelComplexity 模型复杂度
    # detectionConfidence 检测置信度
    # trackingConfidence 追踪置信度
    def __init__(self, mode=False, maxHands=2, modelComplexity=1, detectionCon=0.8, trackCon=0.8):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.modelComplex = modelComplexity
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.tipIds = [4, 8, 12, 16, 20]
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplex, self.detectionCon, self.trackCon)
        # 绘制参数
        self.mpDraw = mp.solutions.drawing_utils
        # 点的样式BGR
        self.handLmStyle = self.mpDraw.DrawingSpec(color=(255, 0, 0), thickness=2)
        # 连接线的样式
        self.handConnStyle = self.mpDraw.DrawingSpec(color=(0, 0, 255), thickness=1)

    # 绘制手部的关节点
    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS, self.handLmStyle,
                                               self.handConnStyle)
        return img

    # 获取手部关节点坐标
    # Text为true可以显示关节点ID，为false不显示
    # Magnify为true可以放大关节点，为false不放大，MagifyID为放大关节点的ID
    def findPosition(self, img, Text=True, Magnify=False, MagifyId=0):
        self.lmList = []
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lmList.append([id, cx, cy])
                    if Text:
                        cv2.putText(img, str(id), (cx - 30, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    if Magnify:
                        cv2.circle(img, (self.lmList[MagifyId][1], self.lmList[MagifyId][2]),
                                   15,
                                   (0, 0, 255),
                                   cv2.FILLED)
        return self.lmList

    # 检测手指是否伸出
    def fingersUp(self):
        fingers = []
        # 大拇指
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 其余手指
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    # 使用cos角判断手指是否伸出
    def fingersUP_cos(self):
        keypoint = []
        for i in self.lmList:
            keypoint.append(i[1:])
        angles = angle_util.pose_to_angles(keypoint)
        return angles

    # 计算手指之间的距离
    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)  # 检测手势并画上骨架信息

        lmList = detector.findPosition(img, Text=True, Magnify=False, MagifyId=0)  # 获取得到坐标点的列表
        if len(lmList) != 0:
            detector.fingersUp()
            detector.fingersUP_cos()

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, 'fps:' + str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv2.imshow('Image', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main()
