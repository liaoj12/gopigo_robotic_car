from __future__ import division
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
from math import *
from gopigo import *

"""
Only calibrate in a certain range, needs more tests on outer range
"""
def set_left_v(v):
  set_left_speed(int(430.02*v+7.3849+2))

def set_right_v(v):
  set_right_speed(int(485.42*v+4.1073))

def turning(r, v, angle, dir='cw', N = 200, w = 0.115):
  set_left_v(v*1.5)
  set_right_v(v*1.5)

  r = r * 4
  t_turn = 2*pi*w/(v*N)
  theta = 2*pi/N
  t_fwd = 0.5*r*cos((pi-theta)/2)/v

  for i in range(int(ceil(angle/theta))):
    if dir == 'cw':
      right()
    elif dir == 'ccw':
      left()
    time.sleep(t_turn)
    fwd()
    time.sleep(t_fwd)

# function moves the car with a given speed
#     v - speed
def grand_go_straight(v):
  set_left_v(v*1.5)
  set_right_v(v*1.5)
  fwd()

class ClosestFace():
  def __init__(self):
    self.x = 0
    self.y = 0
    self.w = 0
    self.h = 0

# During the detection, the rectangle of the face is pretty much a square based
# on the observation of its output, so choose only width to be calculated

diff_torlerence = 3 # needs to be adjusted to be optimal
w_actual= 21 # cm, actual width of the face
w_safe = 21 # have to recalculated since I might did sth wrong
d_desired = 40 # cm, safe distance between face and car
d = 313 # px

(window_width, window_height) = (240, 320)
(h, w) = (320, 240)
center = (w/2, h/2)
M = cv2.getRotationMatrix2D(center, 180, 1.0)

# initialize the camera and grab a reference to the raw camera capture
face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')
camera = PiCamera()
camera.resolution = (w, h)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(w, h))

# allow the camera to warmup
time.sleep(0.1)

counter = 1
grand_go_straight(0.1)
# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
  # grab the raw NumPy array repressenting the image, then initialize the timestamp
  # and occupied/unoccupied text
  image = frame.array

  # Rotate the image
  image = cv2.warpAffine(image, M, (window_width, window_height))

  faces = face_cascade.detectMultiScale(image, 1.1, 5)

  # assume only one face would be detected
  if len(faces) != 0:
    D_act_closet = 100000
    i_max = ClosestFace()
    # finding the closest face/obstacle
    for (x, y, w, h) in faces:
      cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
      D_act = w_actual * d / w
      if D_act < D_act_closet:
        D_act_closet = D_act
        i_max.x = x
        i_max.y = y
        i_max.w = w
        i_max.h = h

    (x, y, w, h) = (i_max.x, i_max.y, i_max.w, i_max.h)
    cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
    #   cv2.imwrite("./Test"+str(counter)+".jpg", image)
    #   counter += 1
    D_act = w_actual * d / w
    d_pix = x+w/2 - window_width / 2
    angle_to_face = abs(atan(d_pix/d))
    angle = pi / 3
    if d_pix > 0:
      direction = 'ccw'
    elif d_pix < 0:
      direction = 'cw'
    turning(0.1, 0.1, angle-angle_to_face, dir=direction)
    #   print "Counter: ", counter
    #   print "x: ", x
    #   print "y: ", y
    #   print "w: ", w
    #   print "h: ", h
    #   print "d_pix: ", d_pix
    #   print "D_actual: ", D_act
    #   print "angle_to_face: ", angle_to_face
    #   print "Direction: ", direction
    #   print

  # clear the stream in preparation for the next frame
  rawCapture.truncate(0)

  # this doesn't work well, ctrl+c works better
  if cv2.waitKey(1) & 0xFF == ord('q'):
    stop()
    break
