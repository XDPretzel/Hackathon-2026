import customtkinter as ctk
import threading
from PIL import Image, ImageDraw
import pystray
import cv2
import time
import subprocess
import mediapipe as mp
import pyautogui
from ui_utils import draw_status, draw_volume_bar
from system_controller import SystemController
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

# Flat black theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("300x300")
        self.configure(fg_color="#1a1a1a")
        self.parent = parent
        
        # Elements
        ctk.CTkLabel(self, text="Media Source:").pack(pady=(20,0))
        ctk.CTkComboBox(self, values=["System Default", "Spotify", "YouTube"]).pack()
        
        ctk.CTkLabel(self, text="Webcam:").pack(pady=(20,0))
        ctk.CTkComboBox(self, values=["Camera 0", "Camera 1"]).pack()
        
        self.tray_var = ctk.BooleanVar(value=parent.minimize_to_tray)
        cb = ctk.CTkCheckBox(self, text="Minimize to tray", variable=self.tray_var, 
                             command=self.update_tray_setting)
        cb.pack(pady=30)
        
    def update_tray_setting(self):
        self.parent.minimize_to_tray = self.tray_var.get()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gesture Control")
        self.geometry("400x500")
        self.configure(fg_color="#121212")  # Flat black

        self.is_tracking = False
        self.is_camera_on = False
        self.minimize_to_tray = False # Changed to False so the app fully closes when clicking X
        self.tray_icon = None
        self.cap = None

        self.sys_ctrl = SystemController()
        self.COOLDOWN = 1.5
        self.SWIPE_SETTLE_TIME = 0.3
        self.SWIPE_THRESHOLD = 0.3
        
        self.last_action_time = 0
        self.status = "READY"
        self.current_vol = self.sys_ctrl.get_system_volume()
        
        # State tracking for gestures
        self.is_adjusting_vol = False
        self.vol_start_y = 0
        self.vol_start_level = 0
        self.win_is_playing = False
        
        self.palm_start_time = 0
        self.is_swiping = False
        self.swipe_start_x = None

        # Top Bar (Settings & Camera Toggle)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(top_frame, text="Settings", width=80, command=self.open_settings).pack(side="left")
        self.cam_btn = ctk.CTkButton(top_frame, text="Show Camera", width=100, command=self.toggle_camera)
        self.cam_btn.pack(side="right")

        # Camera Placeholder (Hidden by default)
        self.cam_label = ctk.CTkLabel(self, text="[Camera Feed]", height=200, fg_color="#222222")

        # Center Power Button
        self.power_btn = ctk.CTkButton(self, text="⏻", width=200, height=200, corner_radius=100,
                                       font=("Segoe UI", 80, "bold"), fg_color="#333333", hover_color="#444444",
                                       command=self.toggle_tracking)
        self.power_btn.pack(expand=True)

        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Auto-start tracking when the app opens
        self.after(500, self.toggle_tracking)

    def toggle_tracking(self):
        self.is_tracking = not self.is_tracking
        if self.is_tracking:
            self.power_btn.configure(fg_color="#00aa00", hover_color="#00cc00")
            self.status = "READY"
            # Start camera if not already running
            if not self.cap:
                self.cap = cv2.VideoCapture(0)
                self.update_camera()
        else:
            self.power_btn.configure(fg_color="#333333", hover_color="#444444")
            self.status = "IDLE"
            # Stop camera only if display is also off
            if not self.is_camera_on and self.cap:
                self.cap.release()
                self.cap = None

    def toggle_camera(self):
        self.is_camera_on = not self.is_camera_on
        if self.is_camera_on:
            self.cam_btn.configure(text="Hide Camera")
            self.cam_label.pack(after=self.power_btn, pady=20, fill="x", padx=20)
            
            # Start OpenCV camera if not already running
            if not self.cap:
                self.cap = cv2.VideoCapture(0)
                self.update_camera()
        else:
            self.cam_btn.configure(text="Show Camera")
            self.cam_label.pack_forget()
            
            # Stop OpenCV camera only if tracking is also off
            if not self.is_tracking and self.cap:
                self.cap.release()
                self.cap = None
            self.cam_label.configure(image=None, text="[Camera Feed]")

    def update_camera(self):
        if (self.is_camera_on or self.is_tracking) and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                
                if self.is_tracking:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb_frame)
                    current_time = time.time()

                    if results.multi_hand_landmarks:
                        # 1. DUAL-HAND HEART GESTURE (MUST BE PRIORITIZED)
                        if len(results.multi_hand_landmarks) == 2:
                            if detect_heart_gesture(results.multi_hand_landmarks):
                                if current_time - self.last_action_time > self.COOLDOWN:
                                    pyautogui.hotkey('command', 'l') 
                                    self.status = "SONG SAVED ❤️"
                                    self.last_action_time = current_time

                        # 2. INDIVIDUAL HAND GESTURES
                        for hand_landmarks in results.multi_hand_landmarks:
                            if self.is_camera_on:
                                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                            # --- VOLUME CONTROL (RELATIVE) ---
                            if is_pinching(hand_landmarks):
                                hand_y = get_hand_y(hand_landmarks)
                                if not self.is_adjusting_vol:
                                    self.is_adjusting_vol = True
                                    self.vol_start_y = hand_y
                                    self.vol_start_level = self.sys_ctrl.get_system_volume()
                                
                                delta_y = self.vol_start_y - hand_y
                                change = int(delta_y / 0.4 * 100)
                                new_vol = max(0, min(100, self.vol_start_level + change))
                                self.sys_ctrl.set_system_volume(new_vol)
                                self.current_vol = new_vol
                                self.status = f"VOLUME: {self.current_vol}%"
                                if self.is_camera_on:
                                    draw_volume_bar(frame, self.current_vol)
                                continue 
                            else:
                                self.is_adjusting_vol = False

                            # --- PALM GESTURES (WITH SETTLE DELAY) ---
                            if play_gesture(hand_landmarks):
                                if self.palm_start_time == 0:
                                    self.palm_start_time = current_time
                                
                                # Wait for settle time before allowing swipe
                                if current_time - self.palm_start_time > self.SWIPE_SETTLE_TIME:
                                    current_x = get_hand_x(hand_landmarks)
                                    
                                    if not self.is_swiping:
                                        self.is_swiping = True
                                        self.swipe_start_x = current_x
                                        self.status = "PALM READY"
                                    
                                    delta_x = current_x - self.swipe_start_x
                                    
                                    if abs(delta_x) > self.SWIPE_THRESHOLD:
                                        if current_time - self.last_action_time > self.COOLDOWN:
                                            if delta_x > 0:
                                                self.sys_ctrl.skip_track()
                                                self.status = "SKIPPING >>"
                                            else:
                                                self.sys_ctrl.previous_track()
                                                self.status = "<< PREVIOUS"
                                            
                                            self.last_action_time = current_time
                                            self.swipe_start_x = current_x 
                                    
                                    # Also check for "Play" while holding palm
                                    elif current_time - self.last_action_time > self.COOLDOWN:
                                        spotify_state = self.sys_ctrl.get_spotify_state()
                                        if spotify_state == "paused" or (spotify_state == "unknown" and not self.win_is_playing):
                                            self.sys_ctrl.play()
                                            self.status = "RESUMING..."
                                            self.win_is_playing = True
                                            self.last_action_time = current_time
                                else:
                                    self.status = "PREPARING PALM..."
                            
                            elif pause_gesture(hand_landmarks):
                                self.palm_start_time = 0
                                self.is_swiping = False
                                self.swipe_start_x = None
                                
                                if current_time - self.last_action_time > self.COOLDOWN:
                                    spotify_state = self.sys_ctrl.get_spotify_state()
                                    if spotify_state == "playing" or (spotify_state == "unknown" and self.win_is_playing):
                                        self.sys_ctrl.pause()
                                        self.status = "PAUSING..."
                                        self.win_is_playing = False
                                        self.last_action_time = current_time
                            else:
                                self.palm_start_time = 0
                                self.is_swiping = False
                                self.swipe_start_x = None
                                if "SAVED" not in self.status and "VOLUME" not in self.status and "PALM" not in self.status:
                                    if current_time - self.last_action_time > 1.0:
                                        self.status = "TRACKING..."
                
                if self.is_camera_on:
                    draw_status(frame, self.status)
                    
                    # Convert color format from BGR (OpenCV) to RGB (PIL)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    
                    # Create CTkImage and update label
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(320, 240))
                    self.cam_label.configure(image=ctk_img, text="")
            
            # Schedule the next frame update in 15ms
            self.after(15, self.update_camera)

    def open_settings(self):
        SettingsWindow(self)

    def on_close(self):
        if self.minimize_to_tray:
            # Re-release camera ONLY if tracking is also OFF
            if not self.is_tracking and self.cap:
                self.cap.release()
                self.cap = None
            self.withdraw()
            self.start_tray()
        else:
            if self.cap:
                self.cap.release()
            self.quit()

    def start_tray(self):
        img = Image.new('RGB', (64, 64), color=(0, 120, 215))
        d = ImageDraw.Draw(img)
        d.ellipse((16, 16, 48, 48), fill=(255, 255, 255))
        
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_window, default=True),
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.tray_icon = pystray.Icon("GestureApp", img, "Gesture App", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon, item):
        self.tray_icon.stop()
        self.after(0, self.deiconify)
        # If camera was supposed to be on, ensure cap is active
        if self.is_camera_on or self.is_tracking:
            self.after(100, self.reinit_camera)

    def reinit_camera(self):
        if (self.is_camera_on or self.is_tracking) and not self.cap:
            self.cap = cv2.VideoCapture(0)
            self.update_camera()

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        if self.cap:
            self.cap.release()
        self.quit()

if __name__ == "__main__":
    App().mainloop()
