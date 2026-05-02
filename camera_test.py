import cv2
import mediapipe as mp
import pyautogui
import time
from ui_utils import draw_status
from gesture_detector import play_gesture, pause_gesture, skip_gesture, previous_gesture

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)

# Settings
COOLDOWN = 2.0  # Seconds between actions
last_action_time = 0
status = "READY"

print("Playback Controller Active. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Flip and convert to RGB for MediaPipe
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_time = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the skeleton
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Check Gestures
            gesture_detected = None
            if play_gesture(hand_landmarks):
                gesture_detected = "PLAY"
            elif pause_gesture(hand_landmarks):
                gesture_detected = "PAUSE"
            #elif skip_gesture(hand_landmarks):
            #    gesture_detected = "SKIP"
            #elif previous_gesture(hand_landmarks):
            #    gesture_detected = "PREVIOUS"

            # Trigger Action if not on cooldown
            if gesture_detected and (current_time - last_action_time > COOLDOWN):
                print(f"Action triggered: {gesture_detected}")
                
                if gesture_detected == "PLAY":
                    pyautogui.press('playpause')
                elif gesture_detected == "PAUSE":
                    pyautogui.press('playpause')
                elif gesture_detected == "SKIP":
                    pyautogui.press('nexttrack')
                elif gesture_detected == "PREVIOUS":
                    pyautogui.press('prevtrack')
                
                status = f"DETECTED: {gesture_detected}"
                last_action_time = current_time
            elif not gesture_detected:
                # Clear status if no gesture is held
                if current_time - last_action_time > 1.0:
                    status = "TRACKING..."

    # Draw the HUD
    draw_status(frame, status)
    cv2.imshow("Playback Controller Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()