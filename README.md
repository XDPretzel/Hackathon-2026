# Gest - Hand Tracking Media Controller 🖐️🎵

Gest is a premium, gesture-based media controller for macOS and Windows. It allows you to control your system volume, play/pause music, and skip tracks using simple hand gestures captured by your webcam.

## Features
- **Volume Control:** Pinch your fingers and move them up/down to adjust system volume.
- **Play/Pause:** Show a flat palm to play/resume, or a closed fist to pause.
- **Skip/Previous:** Swipe your palm to the right to skip, or to the left for the previous track.
- **Minimalist UI:** A sleek, dark-themed interface that stays out of your way.
- **System Tray Integration:** Minimize to the menu bar (macOS) or system tray (Windows) to keep it running in the background.

## Installation & Usage

### Running the Standalone App (macOS)
1.  Navigate to the `dist/` folder.
2.  Launch **`Gest.app`**.
3.  **Permissions:** When prompted, grant the app access to your **Camera** and **Accessibility** features. (Accessibility is required for the app to send media keys like Play/Pause to the system).

### 🛠️ Running from Source
If you want to run the code manually or contribute:
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the App:**
    ```bash
    python main.py
    ```

### 📦 Building the App
To bundle the app yourself using the provided build script:
```bash
python build_standalone.py
```

## Gestures Reference
| Gesture | Action |
| :--- | :--- |
| **Pinch (Index + Thumb)** | Adjust Volume (Move hand up/down) |
| **Flat Palm** | Play / Resume |
| **Closed Fist** | Pause |
| **Swipe Palm Right** | Skip Track >> |
| **Swipe Palm Left** | Previous Track << |

## Troubleshooting
- **Camera Access:** Ensure the app has permissions in *System Settings > Privacy & Security > Camera*.
- **Accessibility:** If media keys (Play/Pause) aren't working, ensure the app (or your Terminal) is enabled in *System Settings > Privacy & Security > Accessibility*.
- **Crash Logs:** If the app fails to start, check `~/gest_crash_log.txt` for details.

---
Built by Ross, Peter, Robert, and Luke for the OSU Hackathon 2026.