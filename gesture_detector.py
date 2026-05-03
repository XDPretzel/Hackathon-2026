#=============== Import libraries ===============
import cv2
import mediapipe as mp
import pyautogui


#=============== Play Gesture detection ===============
def play_gesture():

#=============== Pause Gesture detection ===============
def pause_gesture():
    pass


def is_pointing_up(landmarks):
    """Detects if only the Index finger is pointing up (Number One gesture)"""
    # Index extended (tip y < joint y)
    index_up = landmarks.landmark[8].y < landmarks.landmark[6].y
    # Middle, Ring, Pinky folded down (tip y > joint y)
    others_folded = all([landmarks.landmark[tip].y > landmarks.landmark[tip-2].y for tip in [12, 16, 20]])
    return index_up and others_folded

def get_hand_x(landmarks):
    """Returns the horizontal position of the hand (using the index tip)"""
    return landmarks.landmark[8].x

#=============== Skip Gesture detection ===============
def skip_gesture(landmarks, prev_x):
    """Detects 'Number One' gesture moving Right"""
    if not is_pointing_up(landmarks) or prev_x is None:
        return False
    
    current_x = get_hand_x(landmarks)
    # Movement going right (x increases). Threshold 0.05 can be adjusted.
    return (current_x - prev_x) > 0.05

#=============== Repeat Gesture detection ===============
def repeat_gesture(landmarks):
    """Detects Left Hand index finger pointing Right"""
    # Index tip x > joint x (pointing right) & other fingers folded (tip y > joint y)
    return landmarks.landmark[8].x > landmarks.landmark[6].x and all([landmarks.landmark[tip].y > landmarks.landmark[tip-2].y for tip in [12, 16, 20]])

#=============== Previous Gesture detection ===============
def previous_gesture(landmarks, prev_x):
    """Detects 'Number One' gesture moving Left"""
    if not is_pointing_up(landmarks) or prev_x is None:
        return False
    
    current_x = get_hand_x(landmarks)
    # Movement going left (x decreases). Threshold 0.05 can be adjusted.
    return (prev_x - current_x) > 0.05

#=============== Volume Up Gesture detection ===============
def volume_up_gesture():
    pass

#=============== Volume Down Gesture detection ===============
def volume_down_gesture():
    pass

#=============== Save/Like Gesture detection ===============
def save_like_gesture():
    pass
