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



def get_hand_x(landmarks):
    """Returns the horizontal position of the hand (using the index tip)"""
    return landmarks.landmark[8].x

#=============== Skip Gesture detection ===============
def skip_gesture(landmarks, prev_x):
    """Detects 'Number One' gesture moving Right"""
    if not is_pointing_up(landmarks) or prev_x is None:
        return False
    
    current_x = get_hand_x(landmarks)
    # Movement going right (x increases). Increased threshold for better control.
    return (current_x - prev_x) > 0.15

#=============== Repeat Gesture detection ===============
def repeat_gesture(landmarks):
    """Detects Left Hand hitchhiker gesture (thumb pointing left)"""
    # Thumb tip x < Thumb joint x (pointing left)
    thumb_pointing_left = landmarks.landmark[4].x < landmarks.landmark[2].x
    # Other fingers folded (tip y > joint y)
    fingers_folded = all([landmarks.landmark[tip].y > landmarks.landmark[tip-2].y for tip in [8, 12, 16, 20]])
    return thumb_pointing_left and fingers_folded

#=============== Previous Gesture detection ===============
def previous_gesture(landmarks, prev_x):
    """Detects 'Number One' gesture moving Left"""
    if not is_pointing_up(landmarks) or prev_x is None:
        return False
    
    current_x = get_hand_x(landmarks)
    # Movement going left (x decreases). Increased threshold for better control.
    return (prev_x - current_x) > 0.15

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
def detect_heart_gesture(multi_hand_landmarks):
    """Detects a heart shape formed by two hands (joined thumbs and index fingers)"""
    if len(multi_hand_landmarks) < 2:
        return False
        
    # Get landmarks for both hands
    h1 = multi_hand_landmarks[0].landmark
    h2 = multi_hand_landmarks[1].landmark
    
    # 1. Thumbs (4) should be close to each other (Bottom of heart)
    thumb_dist = ((h1[4].x - h2[4].x)**2 + (h1[4].y - h2[4].y)**2)**0.5
    
    # 2. Index fingers (8) should be close to each other (Top center of heart)
    index_dist = ((h1[8].x - h2[8].x)**2 + (h1[8].y - h2[8].y)**2)**0.5
    
    # 3. Check if hands are roughly at the same height
    y_diff = abs(h1[0].y - h2[0].y)
    
    # 4. CRITICAL: Other fingers (Middle, Ring, Pinky) MUST be folded for a clean heart
    # This prevents Skip/Rewind (pointing up) from being seen as a heart.
    others_folded = True
    for hand in [h1, h2]:
        for tip in [12, 16, 20]:
            if hand[tip].y < hand[tip-2].y: # Finger is extended
                others_folded = False
    
    # Thresholds
    return thumb_dist < 0.1 and index_dist < 0.1 and y_diff < 0.1 and others_folded
