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


#=============== Volume Gesture detection ===============
def is_pinching(landmarks):
    """Detects if Thumb and Index finger are touching (Pinch)"""
    # 4 = Thumb Tip, 8 = Index Tip
    thumb_tip = landmarks.landmark[4]
    index_tip = landmarks.landmark[8]
    
    # Calculate Euclidean distance
    distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
    
    # Threshold for a pinch (found via testing)
    return distance < 0.05

def get_hand_y(landmarks):
    """Returns the vertical position of the hand (using the wrist)"""
    # 0 = Wrist
    return landmarks.landmark[0].y

#=============== Volume Down Gesture detection ===============
def volume_down_gesture():
    pass

#=============== Save/Like Gesture detection ===============
def save_like_gesture():
    pass
