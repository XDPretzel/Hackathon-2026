#=============== Import libraries ===============
import cv2
import mediapipe as mp
import pyautogui


#=============== Play Gesture detection ===============
def play_gesture():
    pass

#=============== Pause Gesture detection ===============
def pause_gesture():
    pass


#=============== Skip Gesture detection ===============
def skip_gesture(landmarks):
    """Detects Left Hand index finger pointing Right"""
    # Index tip x > joint x (pointing right) & other fingers folded (tip y > joint y)
    return landmarks.landmark[8].x > landmarks.landmark[6].x and all([landmarks.landmark[tip].y > landmarks.landmark[tip-2].y for tip in [12, 16, 20]])
#=============== Previous Gesture detection ===============
def previous_gesture():
    pass


#=============== Volume Up Gesture detection ===============
def volume_up_gesture():
    pass

#=============== Volume Down Gesture detection ===============
def volume_down_gesture():
    pass

#=============== Save/Like Gesture detection ===============
def save_like_gesture():
    pass
