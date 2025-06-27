from WePort import *
from WeDCMotor import *
import lcd
import sensor
from ObjectDetection_20 import *
import time
import os

print("Files in internal memory", os.listdir("/flash"))
print("Files in SD", os.listdir("/sd"))

v_20ObjectClassifier = 0	#20ObjectClassifier
v_img = 0	#img
v_IdentifierResult = 0	#IdentifierResult
v_cx = 0	#cx
v_cy = 0	#cy

def f_MoveForward(l_FD):
    dc_1.run(l_FD)
    dc_2.run(l_FD)
    dc_3.run(l_FD * -1)
    dc_4.run(l_FD * -1)

def f_MoveBackward(l_BD):
    dc_1.run(l_BD * -1)
    dc_2.run(l_BD * -1)
    dc_3.run(l_BD)
    dc_4.run(l_BD)

def f_MoveLeft(l_ML):
    dc_1.run(l_ML * -1)
    dc_2.run(l_ML)
    dc_3.run(l_ML)
    dc_4.run(l_ML * -1)

def f_MoveRight(l_MR):
    dc_1.run(l_MR)
    dc_2.run(l_MR * -1)
    dc_3.run(l_MR * -1)
    dc_4.run(l_MR)
#	Init()
def f_Init():
    global v_20ObjectClassifier, v_img, v_IdentifierResult, v_cx, v_cy
    lcd.init(freq=15000000,color=0x0000)
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.run(1)
    sensor.skip_frames(10)
    sensor.set_auto_gain(True)
    sensor.set_auto_whitebal(True)

dc_1 = WeDCMotor(1)
dc_2 = WeDCMotor(2)
dc_3 = WeDCMotor(3)
dc_4 = WeDCMotor(4)

f_Init()
v_20ObjectClassifier = ObjectDetection_20("/sd/face.kmodel", "")
while True:
    print("here")
    v_img = sensor.snapshot()
    v_IdentifierResult = v_20ObjectClassifier.object_detection(v_img)
    if v_IdentifierResult:
        print("VR", v_IdentifierResult)        
        print("here result")    
        v_cx = v_IdentifierResult[2][0]
        v_cy = v_IdentifierResult[2][1]
        v_close = v_IdentifierResult[3][3] > 200
        print(v_cx)
        print(v_cy)
        if v_close:
            print("close")
            f_MoveBackward(100)
        elif v_cx > 120 and v_cx < 200:
            f_MoveForward(20)
            time.sleep(0.01)
        elif v_cx < 120:
            f_MoveLeft(80)
            time.sleep(0.01)
        elif v_cx > 200:
            f_MoveRight(80)
            time.sleep(0.01)
        else:
            f_MoveForward(0)
    else:
        f_MoveForward(0)