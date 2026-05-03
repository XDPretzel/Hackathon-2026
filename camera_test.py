import cv2
import mediapipe as mp
import pyautogui
import time
import subprocess
from ui_utils import draw_status, draw_volume_bar
from gesture_detector import (
    play_gesture, pause_gesture, skip_gesture, previous_gesture, 
    is_pinching, get_hand_y, detect_heart_gesture, is_pointing_up, get_hand_x
)

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7, 
    min_tracking_confidence=0.7
)

def get_system_volume():
    """Get current Computer volume (0-100)"""
    try:
        cmd = "osascript -e 'output volume of (get volume settings)'"
        return int(subprocess.check_output(cmd, shell=True).decode().strip())
    except: return 50

def set_system_volume(volume):
    """Set Computer volume (0-100)"""
    try: subprocess.run(f"osascript -e 'set volume output volume {volume}'", shell=True)
    except: pass

def get_spotify_state():
    """Returns 'playing', 'paused', or 'stopped'"""
    try:
        cmd = "osascript -e 'tell application \"Spotify\" to player state as string'"
        return subprocess.check_output(cmd, shell=True).decode().strip().lower()
    except:
        return "unknown"

cap = cv2.VideoCapture(0)

# Settings
COOLDOWN = 1.5
SWIPE_THRESHOLD = 0.2 
SWIPE_SETTLE_TIME = 0.4 # Must hold palm for 0.4s before swipe can start
last_action_time = 0
status = "READY"
current_vol = get_system_volume()

# Tracking state
is_adjusting_vol = False
vol_start_y = 0
vol_start_level = 0

swipe_start_x = None
palm_start_time = 0
is_swiping = False

print("Deliberate Controller Active. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    current_time = time.time()

    if results.multi_hand_landmarks:
        # 1. DUAL-HAND HEART GESTURE
        if len(results.multi_hand_landmarks) == 2:
            if detect_heart_gesture(results.multi_hand_landmarks):
                if current_time - last_action_time > COOLDOWN:
                    pyautogui.hotkey('command', 'l') 
                    status = "SONG SAVED ❤️"
                    last_action_time = current_time

        # 2. INDIVIDUAL HAND GESTURES
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- VOLUME CONTROL (RELATIVE) ---
            if is_pinching(hand_landmarks):
                hand_y = get_hand_y(hand_landmarks)
                if not is_adjusting_vol:
                    is_adjusting_vol = True
                    vol_start_y = hand_y
                    vol_start_level = get_system_volume()
                
                delta_y = vol_start_y - hand_y
                change = int(delta_y / 0.4 * 100)
                new_vol = max(0, min(100, vol_start_level + change))
                set_system_volume(new_vol)
                current_vol = new_vol
                status = f"VOLUME: {current_vol}%"
                draw_volume_bar(frame, current_vol)
                continue 
            else:
                is_adjusting_vol = False

            # --- PALM GESTURES (WITH SETTLE DELAY) ---
            if play_gesture(hand_landmarks):
                if palm_start_time == 0:
                    palm_start_time = current_time
                
                # Wait for settle time before allowing swipe
                if current_time - palm_start_time > SWIPE_SETTLE_TIME:
                    current_x = get_hand_x(hand_landmarks)
                    
                    if not is_swiping:
                        is_swiping = True
                        swipe_start_x = current_x
                        status = "PALM READY"
                    
                    delta_x = current_x - swipe_start_x
                    
                    if abs(delta_x) > SWIPE_THRESHOLD:
                        if current_time - last_action_time > COOLDOWN:
                            if delta_x > 0:
                                subprocess.run("osascript -e 'tell application \"Spotify\" to next track'", shell=True)
                                status = "SKIPPING >>"
                            else:
                                subprocess.run("osascript -e 'tell application \"Spotify\" to previous track'", shell=True)
                                status = "<< PREVIOUS"
                            
                            last_action_time = current_time
                            swipe_start_x = current_x 
                    
                    # Also check for "Play" while holding palm
                    elif current_time - last_action_time > COOLDOWN:
                        spotify_state = get_spotify_state()
                        if spotify_state == "paused":
                            subprocess.run("osascript -e 'tell application \"Spotify\" to play'", shell=True)
                            status = "RESUMING..."
                            last_action_time = current_time
                else:
                    status = "PREPARING PALM..."
            
            elif pause_gesture(hand_landmarks):
                palm_start_time = 0
                is_swiping = False
                swipe_start_x = None
                
                if current_time - last_action_time > COOLDOWN:
                    spotify_state = get_spotify_state()
                    if spotify_state == "playing":
                        subprocess.run("osascript -e 'tell application \"Spotify\" to pause'", shell=True)
                        status = "PAUSING..."
                        last_action_time = current_time
            else:
                palm_start_time = 0
                is_swiping = False
                swipe_start_x = None
                if "SAVED" not in status and "VOLUME" not in status and "PALM" not in status:
                    status = "TRACKING..."

    draw_status(frame, status)
    cv2.imshow("Hand Controller", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv2.destroyAllWindows()