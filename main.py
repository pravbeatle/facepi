from gpiozero import MotionSensor
import time
pir = MotionSensor(6)
while True:
  if pir.motion_detected:
    print("Motion Detected!!")
    time.sleep(60)
