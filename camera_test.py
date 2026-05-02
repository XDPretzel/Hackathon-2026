import cv2
from ui_utils import draw_status

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam.")
    exit()

print("Camera active. Press 's' to simulate a gesture, 'q' to quit.")
status = "READY"

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame could not be read...")
        break

    # Simulate a status change for testing
    key = cv2.waitKey(1) & 0xFF
    if key == ord("s"):
        status = "GESTURE DETECTED!"
    elif key == ord("q"):
        break

    # Draw the green status in the corner
    draw_status(frame, status)

    cv2.imshow("Camera Test", frame)

cap.release()
cv2.destroyAllWindows()