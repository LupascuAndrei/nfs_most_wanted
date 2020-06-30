from keys import PressKey, ReleaseKey, up, left, down, right
import time
import keyboard
import mss

sct = mss.mss()

while (True):
    key = 0xC8 
    PressKey(key)
    time.sleep(0.5)
    ReleaseKey(key)
    time.sleep(0.5)
    if keyboard.is_pressed('q'):
        print('da')
    
        #

        # cv2.decstroyAllWindows()
        quit()
