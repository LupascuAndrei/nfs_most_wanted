from keys import PressKey, ReleaseKey, up, left, down, right, nitro
import time
import keyboard
import mss
import numpy as np
import cv2
import win32api
import sys, os
from datetime import datetime

today = datetime.now()
timeString = today.strftime('%b_%d_%Y__%H_%M_%S')
writeVideo = ( len(sys.argv) > 1 and sys.argv[1] == 'save' ) 

width = 1920
height = 1080

aiHeight = int(height/2)
aiWidth = int(width/2)
frame = None

videoFrames = []


    
# save gameplay output for premiere pro editing
if(writeVideo):
    outputDir = './out/' + timeString
    os.mkdir(outputDir)

    fourcc1 = cv2.VideoWriter_fourcc(*'XVID')
    outGame = cv2.VideoWriter(outputDir + '/game.avi', fourcc1, 25, (width, height))
    videoFrames.append(outGame)

    fourcc2 = cv2.VideoWriter_fourcc(*'XVID')
    outResult = cv2.VideoWriter(outputDir + '/result.avi', fourcc2, 25, (aiWidth, aiHeight))
    videoFrames.append(outResult)

    fourcc3 = cv2.VideoWriter_fourcc(*'XVID')
    outOriginal = cv2.VideoWriter(outputDir + '/original.avi', fourcc3, 25, (width, height))
    videoFrames.append(outOriginal)


import threading, queue

resultAviQueue = queue.Queue()
gameAviQueue = queue.Queue()
originalAviQueue = queue.Queue()

processEnded = False
def threadedWriteToFile():
    global processEnded
    while not processEnded:
        # print('da')
        try:
            #print('citesc')
            data = resultAviQueue.get()
            outResult.write(data)
            resultAviQueue.task_done()

            data = gameAviQueue.get()
            outGame.write(data)
            gameAviQueue.task_done()

            data = originalAviQueue.get()
            outOriginal.write(data)
    
        except:
            pass
if writeVideo:
    thread = threading.Thread(target = threadedWriteToFile)
    thread.start()

isDebug = len(sys.argv)>1 and sys.argv[1] == 'debug'
screenHeight = win32api.GetSystemMetrics(1)
screenWidth = win32api.GetSystemMetrics(0)

def quit(): 
    global processEnded
    processEnded = True
    if writeVideo:
        thread.join()
    for videoFrame in videoFrames:
        videoFrame.release()
    cv2.destroyAllWindows()
    exit()

'''
I'm displaying my game at the top right corner of my screen
'''

gameScreen = {'top': 25, 'left': 0, 'width': width, 'height': height}

def region_of_interest(img, vertices):
    mask = np.zeros_like(img)
    match_mask_color = 255 # <-- This line altered for grayscale.
    
    cv2.fillPoly(mask, vertices, match_mask_color)
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image




lastKeypressConfig = {
    up: False,
    left: False,
    down: False,
    right: False,
}

delayBetweenInputs = 0.08 #seconds

mp = {
    up: 'up',
    down: 'down',
    left: 'left',
    right: 'right'
}

speed = 0
speedLimit = 400
road = []
def changeKeyState(newPressConfig):
    global speed, frame

    pressed = {
        up: False,
        down: False,
        left: False,
        right: False,
        nitro: False
    }
    if (speed < speedLimit * 8/10 and len(road) > 0 and abs(road[0]) < 2 ):
        # current speed is much lower than our desired speed, nitro up !
        PressKey(up)
        PressKey(nitro)
        ReleaseKey(down)
        pressed[up] = True
        pressed[nitro] = True
    elif (speed < speedLimit ):
        # push the pedal but no nitro
        PressKey(up)
        ReleaseKey(down)
        ReleaseKey(nitro)
        pressed[up] = True
    
    elif (speed < speedLimit * 12/10):
        # release both buttons, stop speeding
        ReleaseKey(up)
        ReleaseKey(down)
        ReleaseKey(nitro)
    else:
        # slow down 
        ReleaseKey(up)
        PressKey(down)
        ReleaseKey(nitro)
        pressed[down] = True

    # lastKeypressConfig = what was pressed in the last frame
    for key in lastKeypressConfig:
        if not lastKeypressConfig[key] and key not in newPressConfig:
            continue

        # fresh press
        elif not lastKeypressConfig[key]:
            lastKeypressConfig[key] = newPressConfig[key]
            PressKey(key)
            pressed[key] = True
            continue
        
        # force delayBetweenInputs
        elif lastKeypressConfig[key] + delayBetweenInputs < time.time():
            if key in newPressConfig and newPressConfig[key]:
                lastKeypressConfig[key] = newPressConfig[key]
                PressKey(key)
                pressed[key] = True
            else: 
                ReleaseKey(key)
                lastKeypressConfig[key] = False
            continue
        # delayBetweenInputs ended, release
        elif lastKeypressConfig[key] < time.time():
            if ReleaseKey(key):
                pass
    

    font                   = cv2.FONT_HERSHEY_SIMPLEX
    fontScale              = 0.8
    fontColor              = (255,255,255)
    lineType               = 3

    # visualize what buttons are pressed
    visualButtons = [('up', (400,450), pressed[up]),
                ('down', (400, 500), pressed[down]),
                ('left', (325, 500), pressed[left]),
                ('right', (500, 500), pressed[right]),
                ('nitro', (575, 475), pressed[nitro]),
                (str(speed) + ' km/h', (625, 450), False) ]
    for visual in visualButtons:

        cv2.putText(frame,visual[0], 
            visual[1], 
            font, 
            fontScale,
            (255,0 ,0) if visual[2] else (255,255,255),
            lineType)



def pixelAroundCoord(img, coord):
    searchSize = 6
    for i in range(searchSize):
        step = - int(searchSize/2) + i
        if img[coord[1] + step][coord[0]] == 255:
            return True
        if img[coord[1]][coord[0] + step] == 255:
            return True
    return False


# for a rectangle, it detects all possible line combinations for digital alarm clock font numbers
# and hardcodes all line combinations for each number
# i.e. two vertical right lines mean a "1"
def getImageDigitalNumber(img, name):
    h, w = img.shape[0:2]

    lines = []
    totalLines = 0

    spotsToCheck = [
        (h * 0.14 , w * 0.5), # middle top
        (h * 0.82 , w * 0.5), # middle bottom
        (h * 0.42 , w * 0.5), # middle center
        (h * 0.64 , w * 0.21), # bottom left 
        (h * 0.27, w * 0.21), # top left 
        (h * 0.64, w * 0.84), # bottom right
        (h * 0.27, w * 0.84), # top right 
    ]
    for coordFloat in spotsToCheck:
        coord = (int(coordFloat[1]), int(coordFloat[0]))
        isLine = pixelAroundCoord(img, coord)
        totalLines += isLine
        lines.append(isLine)
        cv2.circle(img, coord, 1, (255, 125, 122), 1 )

    if totalLines == 7:
        return 8
    if totalLines == 6:
        if not lines[2]:
            return 0
        if not lines[3]:
            return 9
        if not lines[-1]:
            return 6
    if totalLines == 5:
        if not lines[-1] and not lines[3]:
            return 5
        if not lines[-2] and not lines[4]:
            return 2
        if not lines[3] and not lines[4]:
            return 3
    if totalLines == 4:
        if not lines[0] and not lines[1] and not lines[3]:
            return 4
    if totalLines == 3:
        if lines[-1] and lines[-2] and lines[0]:
            return 7
    if totalLines == 2:
        if lines[-1] and lines[-2]:
            return 1
    return 0 

#https://campushippo.com/lessons/detect-highway-lane-lines-with-opencv-and-python-21438a3e2
def rgbToHsv(rgb):
    return  cv2.cvtColor(np.uint8([[205, 207, 27]]), cv2.COLOR_BGR2HSV)[0][0]


def getRoadIndex(index):
    if len(road) == 0:
        return 0
    if len(road) > index:
        return road[index]
    return road[-1]

def getRoadDiff(pts):
    if (len(road)==0):
        return 0
    s = abs(road[0])
    for i in range(1, min(len(road), pts)):
        s += abs(road[i] - road[i-1])
    return s


sct = mss.mss()
while (True):

    # sct = mss.mss(), a python module for capturing our windows screen
    #  <gameScreen> contains our Most Wanted screen size and position 
    screen = np.array(sct.grab(gameScreen)) # grab screen
    screen = np.flip(screen[:, :, :3], 2) # format for openCV
    screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB) # change to RGB

    #frame = screen
    frame = cv2.resize(screen.copy(), (aiWidth, aiHeight))

    minimapCenterX = int(aiWidth * 11.5/100 ) - 1 
    minimapCenterY = int(aiHeight * 79.2/100) 
    minimapSize =  75
    cv2.rectangle(frame, (minimapCenterX - minimapSize, minimapCenterY - minimapSize), (minimapCenterX + minimapSize, minimapCenterY), (255, 0, 0), 1)


    minimap = frame[minimapCenterY - minimapSize: minimapCenterY,  minimapCenterX - minimapSize: minimapCenterX + minimapSize]

    
    lower, upper = [190, 190, 190], [220, 220, 220]

    mask = None
    tmpMask = None
    tmpMask = cv2.inRange(minimap, np.array(lower), np.array(upper))

    minimapHeight, minimapWidth, channels = minimap.shape

    #get minimap centers
    minimapRoadPoints = []
    curCenterX = int(minimapWidth/2) + 2
    curCenterY = int(minimapHeight) - 2

    minimapLinePoints = 15
    minimapSpaceBetweenPoints = 4 #pixels

    minimapRoadPoints.append((curCenterX, curCenterY))

    # compute the minimap road ahead as an array of points; road direction will be 
    # the incremental difference between points' X coordinate
    for i in range(minimapLinePoints):

        curCenterY -= minimapSpaceBetweenPoints

        rows = 70
        cols = 70
        rows, cols, sumX, sumY, cnt = 3, 30, 0, 0, 0
        # get center of current object
        for i in range(rows):
            for j in range(cols):
                x = int(curCenterX + j - cols/2)
                y = int(curCenterY + i - rows/2)
                if x < 0 or x >= minimapWidth or y < 0 or y >= minimapHeight:
                    continue
                val = tmpMask[y, x]
                if val:
                    sumX += x
                    sumY += y
                    cnt += 1
        if cnt < 1:
            cv2.circle(minimap, (curCenterX, curCenterY), 10, (250, 0, 0))
            continue
        curCenterX = int(sumX/cnt)
        minimapRoadPoints.append((curCenterX, curCenterY))

    # road[i] = holds the X axis difference between the i'th minimap point and our player
    road = []
    for i in range(1, min(len(minimapRoadPoints), 15)):
        road.append(minimapRoadPoints[i][0] - minimapRoadPoints[0][0])

    newPressConfig = {
    }

    roadLen = len(road);
    
    # get current speed
    speeUiCenterX = int(aiWidth * 88.5/100 )
    speeUiCenterY = int(aiHeight * 88/100) 
    speedUiSize =  30
    cv2.rectangle(frame, (speeUiCenterX - speedUiSize, speeUiCenterY - speedUiSize), (speeUiCenterX + speedUiSize, speeUiCenterY), (255, 0, 0), 1)

    speedUi = frame[speeUiCenterY - speedUiSize: speeUiCenterY,  speeUiCenterX - speedUiSize: speeUiCenterX + speedUiSize]
    
    lowerSpeedUiMask, upperSpeedUiMask = [2, 5, 5], [21, 25, 30]
    speedUiMask = cv2.inRange(speedUi, np.array(lowerSpeedUiMask), np.array(upperSpeedUiMask))

    speedUiHeight, speedUiWidth = speedUiMask.shape[0:2]
    
    # apply the same algorithm for all 3 digits
    speed = getImageDigitalNumber(speedUiMask[0:speedUiHeight, 0:int(speedUiWidth/3)], 'speed_1')
    speed = speed * 10 + getImageDigitalNumber(speedUiMask[0:speedUiHeight, int(speedUiWidth/3):int(speedUiWidth*2/3)], 'speed_2')
    speed = speed * 10 + getImageDigitalNumber(speedUiMask[0:speedUiHeight, int(speedUiWidth*2/3):int(speedUiWidth*3/3)], 'speed_3')
    
    delayBetweenInputs = 0.2
    # break on first conditional met
    while(True): 
        if (roadLen == 0):
            break

        val = road[0]
        absVal = abs(val) # first minimap point's orientation (-value means left, 0 means straight ahead, +value means right)

        if absVal == 0:
            break

        key = right if val > 0 else left

        # finetuning for certain speeds and roads
        if speed < 90:
            newPressConfig[key] = time.time() + 0.05 * absVal * speed / 300
            speedLimit = 120
        elif speed < 110:
            newPressConfig[key] = time.time() + 0.015 * absVal 
            speedLimit = 140
        elif speed < 130:
            newPressConfig[key] = time.time() + 0.02 * max(absVal, 2)
            speedLimit = 175
        elif speed < 180: 
            speedLimit = 175


            if (abs(getRoadIndex(3)) > 15):
                speedLimit = 140
                key = right if  getRoadIndex(3) > 0 else left

            if absVal > 0:
                if (absVal == 1 and roadLen > 2 and abs(road[2]) < 4):
                    newPressConfig[key] = time.time() + 0.06
                elif (absVal == 2 and roadLen > 2 and abs(road[2]) < 6):
                    newPressConfig[key] = time.time() + 0.1
                elif absVal < 5:
                    newPressConfig[key] = time.time() + 0.025 * absVal
                elif absVal >= 5:
                    speedLimit = 140
                    newPressConfig[key] = time.time() + 0.035 * absVal
            
            if roadLen > 6 and abs( getRoadIndex(5)) < 12:
                speedLimit = 220
        
        elif speed < 555:

            speedLimit = 220

            absVal2 = abs(getRoadIndex(4))
            if absVal2 > 0:

                if absVal2 >=8 or absVal >= 4:
                    speedLimit = 175
                    newPressConfig[key] = time.time() + 0.3
                elif (absVal2 < 7):
                    newPressConfig[key] = time.time() + 0.05 * absVal2
                else:
                    speedLimit = 175
                    newPressConfig[key] = time.time() + 0.3
    

        elif False:
            if (absVal < 2):
                break

            valFuture = getRoadIndex(1) - getRoadIndex(0) 
            absValFuture = abs(valFuture)

            delayBetweenInputs = 0.2
            roadDiff = getRoadDiff(12)
            accelerating = False
            if (roadLen <= 6 or getRoadDiff(12) > 35):
                speedLimit = 160
            elif (getRoadDiff(12) > 20):
                speedLimit = min(200, speed + 5)
            else:
                speedLimit = 250
                accelerating = True

            if(absValFuture <= 3 and getRoadIndex(2) < 6):
                newPressConfig[key] = time.time() + 0.07 * absValFuture
                break
            else:
                if (absValFuture > 6):
                    speedLimit = speed + 5 #dont slow down but dont speed up
                newPressConfig[key] = time.time() + 0.12 * absValFuture
        
        break

    for i in range(len(minimapRoadPoints) - 1):
        cv2.line(
            minimap,
            minimapRoadPoints[i], minimapRoadPoints[i+1],
            (200, 0, 240), 
        2)



    changeKeyState(newPressConfig)

    # debug current frame
    cv2.imshow('frame', frame)

    if writeVideo:
        originalAviQueue.put(screen)
        gameAviQueue.put(cv2.resize(frame, (width, height)))
        resultAviQueue.put(cv2.resize(minimap, (aiWidth, aiHeight)))
        pass

    cv2.waitKey(1)
    if keyboard.is_pressed('q'):
        quit()