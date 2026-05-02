#=============== Import libraries ===============
import cv2
import mediapipe as mp
import pyautogui


#=============== Play Gesture detection ===============
def play_gesture(landmarks):
    """Detects an Open Hand (4 fingers extended)"""
    # tips: 8, 12, 16, 20 | joints: 6, 10, 14, 18
    return all([landmarks.landmark[tip].y < landmarks.landmark[tip-2].y for tip in [8, 12, 16, 20]])


#=============== Pause Gesture detection ===============
def pause_gesture(landmarks):
    """Detects a Closed Fist (4 fingers curled)"""
    return all([landmarks.landmark[tip].y > landmarks.landmark[tip-2].y for tip in [8, 12, 16, 20]])


#=============== Skip Gesture detection ===============
def skip_gesture():
    pass

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
