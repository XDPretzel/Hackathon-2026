import cv2
import mediapipe as mp
import pyautogui
import time
import subprocess
from ui_utils import draw_status, draw_volume_bar
from gesture_detector import play_gesture, pause_gesture, skip_gesture, previous_gesture, is_pinching, get_hand_y

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

def get_system_volume():
    """Get current Computer volume (0-100)"""
    try:
        cmd = "osascript -e 'output volume of (get volume settings)'"
        return int(subprocess.check_output(cmd, shell=True).decode().strip())
    except:
        return 50

def set_system_volume(volume):
    """Set  Computer volume (0-100)"""
    try:
        subprocess.run(f"osascript -e 'set volume output volume {volume}'", shell=True)
    except:
        pass

cap = cv2.VideoCapture(0)

# Settings
COOLDOWN = 2.0
last_action_time = 0
status = "READY"
current_vol = get_system_volume()

print("Full Controller Active. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    # Flip and convert to RGB for MediaPipe
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    current_time = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- VOLUME CONTROL (PINCH) ---
            if is_pinching(hand_landmarks):
                # Get hand height (0.0 to 1.0)
                hand_y = get_hand_y(hand_landmarks)
                
                # Map hand_y to volume percentage
                # Hand at Y=0.8 (bottom) -> 0%
                # Hand at Y=0.2 (top) -> 100%
                # Formula: (0.8 - hand_y) / (0.8 - 0.2) * 100
                new_vol = int((0.8 - hand_y) / 0.6 * 100)
                new_vol = max(0, min(100, new_vol)) # Keep in bounds
                
                set_system_volume(new_vol)
                current_vol = new_vol
                status = f"VOLUME: {current_vol}%"
                
                # Draw the visual feedback
                draw_volume_bar(frame, current_vol)
            else:
                # --- PLAYBACK GESTURES (IF NOT PINCHING) ---
                gesture = None
                if play_gesture(hand_landmarks): gesture = "PLAY"
                elif pause_gesture(hand_landmarks): gesture = "PAUSE"
                
                if gesture and (current_time - last_action_time > COOLDOWN):
                    pyautogui.press('playpause')
                    status = f"DETECTED: {gesture}"
                    last_action_time = current_time
                elif not gesture and (current_time - last_action_time > 1.0):
                    status = "TRACKING..."

    # Draw the HUD
    draw_status(frame, status)
    cv2.imshow("Hand Controller", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv2.destroyAllWindows()