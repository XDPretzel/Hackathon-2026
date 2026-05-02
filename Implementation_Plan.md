# Hand Gesture Media Controller

This project will allow you to control media playback (Spotify, YouTube, Apple Music) using hand gestures captured by your webcam.

We will break the project down into three main components: Hand Tracking, Gesture Recognition, and System Action Triggering.

## Open Questions
- Do you want to use universal media keys (which will control whatever is currently playing, like Spotify or YouTube), or do you want to specifically target a single application (like Spotify) via AppleScript? Universal media keys are usually the best choice.
- Have you verified that your `camera_test.py` script is working and capturing your webcam feed successfully?
- The current `requirements.txt` has `pygame`, but we will likely want to use `pynput` instead for simulating global media keystrokes. Are you okay with switching to/adding `pynput`?

## Proposed Changes

### Hand Tracking & Recognition
We will use Google's MediaPipe library, which can accurately detect 21 3D landmarks on a hand from a single video frame. 

- **Extracting Landmarks:** In the webcam loop, we pass the frame to MediaPipe to find the coordinates of fingers and joints.
- **Defining Gestures:** By measuring the relative positions of the landmarks, we can define logic for gestures. For example:
  - **Play/Pause:** Open hand (all fingers extended).
  - **Next Track:** Swipe right or point index finger to the right.
  - **Previous Track:** Swipe left or point index finger to the left.
  - **Volume Control:** Pinching index finger and thumb together, then moving hand up or down.

### System Control (pynput)
We will add `pynput` to our project to simulate pressing the Mac media keys (Play/Pause, Next, Previous, Volume Up/Down). These simulate pressing the physical buttons on your keyboard, so they will control Spotify, YouTube (via the browser), or any active media.

#### [MODIFY] [requirements.txt](file:///Users/rossbaldwin/Desktop/Hackathon-2026/requirements.txt)
- Add `pynput` for media control.

#### [NEW] [gesture_detector.py](file:///Users/rossbaldwin/Desktop/Hackathon-2026/gesture_detector.py)
- Integrate the loop from `camera_test.py`.
- Initialize `mediapipe.solutions.hands`.
- Add logic to convert hand landmarks to gestures.
- Add an action mapping system to trigger the `pynput` media key commands when a gesture is recognized. We will need to implement a cooldown so holding a gesture doesn't trigger it 100 times per second.

## Verification Plan

### Automated Tests
- N/A - we will rely on manual visual testing for this application.

### Manual Verification
- Run `gesture_detector.py` and see the webcam feed.
- Perform the "Play/Pause" gesture and ensure music starts or stops.
- Test tracking accuracy in different lighting conditions.
- Ensure the cooldown system prevents actions from firing repeatedly.
