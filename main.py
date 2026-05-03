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
    is_pinching, get_hand_y, is_pointing_up, get_hand_x
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
        self.title("Configuration")
        self.geometry("340x400")
        self.configure(fg_color="#0f0f0f")
        self.parent = parent
        
        # Ensure window is on top
        self.attributes("-topmost", True)
        self.after(10, self.lift)
        self.focus_force()

        # Header
        ctk.CTkLabel(self, text="PREFERENCES", font=("Segoe UI", 14, "bold"), text_color="#555555").pack(pady=(20, 10))
        
        # Container
        container = ctk.CTkFrame(self, fg_color="#181818", corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Media Source
        ctk.CTkLabel(container, text="Media Control Source", font=("Segoe UI", 12)).pack(pady=(20, 5))
        self.source_box = ctk.CTkComboBox(container, values=["System Default", "Spotify", "YouTube"], 
                                          fg_color="#222222", border_color="#333333", button_color="#333333")
        self.source_box.pack(padx=20, fill="x")
        
        # Camera Source
        ctk.CTkLabel(container, text="Input Device", font=("Segoe UI", 12)).pack(pady=(15, 5))
        self.cam_box = ctk.CTkComboBox(container, values=["Camera 0", "Camera 1"],
                                       fg_color="#222222", border_color="#333333", button_color="#333333")
        self.cam_box.pack(padx=20, fill="x")
        
        # Tray Setting
        self.tray_var = ctk.BooleanVar(value=parent.minimize_to_tray)
        ctk.CTkCheckBox(container, text="Minimize to System Tray", variable=self.tray_var, 
                        font=("Segoe UI", 12), command=self.update_tray_setting,
                        fg_color="#00aa00", hover_color="#008800").pack(pady=30)
        
        # Close Button
        ctk.CTkButton(self, text="Done", command=self.destroy, fg_color="#333333", hover_color="#444444").pack(pady=(0, 20))

    def update_tray_setting(self):
        self.parent.minimize_to_tray = self.tray_var.get()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gest")
        self.geometry("450x650")
        self.configure(fg_color="#0a0a0a")  # Deep onyx

        # Core State
        self.is_tracking = False
        self.is_camera_on = False
        self.minimize_to_tray = True 
        self.tray_icon = None
        self.cap = None

        # Logic State
        self.sys_ctrl = SystemController()
        self.COOLDOWN = 1.5

        #SWIPING SENSITIVITY 
        self.SWIPE_SETTLE_TIME = 0.2
        self.SWIPE_THRESHOLD = 0.25
        
        self.last_action_time = 0
        self.status = "SYSTEM STANDBY"
        self.current_vol = self.sys_ctrl.get_system_volume()
        
        self.is_adjusting_vol = False
        self.vol_start_y = 0
        self.vol_start_level = 0
        self.win_is_playing = False
        self.palm_start_time = 0
        self.is_swiping = False
        self.swipe_start_x = None

        # --- UI LAYOUT ---
        
        # Header Area
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=30, pady=(30, 10))
        
        self.title_label = ctk.CTkLabel(self.header, text="GEST", font=("Segoe UI", 24, "bold"), text_color="#ffffff")
        self.title_label.pack(side="left")
        
        self.settings_btn = ctk.CTkButton(self.header, text="⚙", width=40, height=40, corner_radius=20,
                                          fg_color="#181818", hover_color="#222222", font=("Segoe UI", 18),
                                          command=self.open_settings)
        self.settings_btn.pack(side="right")

        # Main Interaction Area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=30)

        # Camera Container (Stylized)
        self.cam_container = ctk.CTkFrame(self.content_frame, fg_color="#121212", corner_radius=20, border_width=1, border_color="#222222")
        self.cam_label = ctk.CTkLabel(self.cam_container, text="CAMERA INACTIVE", font=("Segoe UI", 10), text_color="#444444")
        self.cam_label.pack(fill="both", expand=True, padx=2, pady=2)
        # Hidden by default, shown via toggle_camera
        
        # Power Button Container
        self.button_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.button_container.pack(expand=True)

        self.power_btn = ctk.CTkButton(self.button_container, text="⏻", width=180, height=180, corner_radius=90,
                                       font=("Segoe UI", 70), fg_color="#181818", hover_color="#222222",
                                       border_width=2, border_color="#333333",
                                       command=self.toggle_tracking)
        self.power_btn.pack()

        self.status_label = ctk.CTkLabel(self.button_container, text=self.status, font=("Segoe UI", 12, "bold"), 
                                         text_color="#666666", pady=20)
        self.status_label.pack()

        # Bottom Bar
        self.bottom_bar = ctk.CTkFrame(self, fg_color="#0f0f0f", height=60, corner_radius=0)
        self.bottom_bar.pack(fill="x", side="bottom")
        
        self.cam_toggle_btn = ctk.CTkButton(self.bottom_bar, text="VIEW FEED", font=("Segoe UI", 11, "bold"),
                                            fg_color="transparent", hover_color="#181818", text_color="#888888",
                                            command=self.toggle_camera)
        self.cam_toggle_btn.pack(side="left", padx=20, pady=10)
        
        self.vol_display = ctk.CTkLabel(self.bottom_bar, text=f"VOL: {self.current_vol}%", font=("Segoe UI", 11, "bold"), text_color="#444444")
        self.vol_display.pack(side="right", padx=20)

        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Auto-start tracking when the app opens
        self.after(500, self.toggle_tracking)

    def toggle_tracking(self):
        self.is_tracking = not self.is_tracking
        if self.is_tracking:
            self.power_btn.configure(fg_color="#0a2a0a", border_color="#00ff66", text_color="#00ff66", hover_color="#0f3f0f")
            self.status = "SYSTEM ACTIVE"
            self.status_label.configure(text_color="#00ff66")
            self.ensure_camera_active()
        else:
            self.power_btn.configure(fg_color="#181818", border_color="#333333", text_color="#ffffff", hover_color="#222222")
            self.status = "SYSTEM STANDBY"
            self.status_label.configure(text_color="#666666")
            # Stop camera only if display is also off
            if not self.is_camera_on and self.cap:
                self.cap.release()
                self.cap = None

    def toggle_camera(self):
        self.is_camera_on = not self.is_camera_on
        if self.is_camera_on:
            self.cam_toggle_btn.configure(text="CLOSE FEED", text_color="#ffffff")
            self.cam_container.pack(before=self.button_container, pady=(0, 20), fill="x")
            self.ensure_camera_active()
        else:
            self.cam_toggle_btn.configure(text="VIEW FEED", text_color="#888888")
            self.cam_container.pack_forget()
            
            # Stop OpenCV camera only if tracking is also off
            if not self.is_tracking and self.cap:
                self.cap.release()
                self.cap = None

    def update_camera(self):
        if (self.is_camera_on or self.is_tracking) and self.cap and self.cap.isOpened():
            self._loop_active = True
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                
                if self.is_tracking:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb_frame)
                    current_time = time.time()

                    if results.multi_hand_landmarks:
                        # INDIVIDUAL HAND GESTURES
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

                                # Sensitivity of Volume Control
                                change = int(delta_y / 0.35 * 100)
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
                                if "VOLUME" not in self.status and "PALM" not in self.status:
                                    if current_time - self.last_action_time > 1.0:
                                        self.status = "TRACKING..."
                
                # Update Status Labels
                self.status_label.configure(text=self.status)
                self.vol_display.configure(text=f"VOL: {self.current_vol}%")

                if self.is_camera_on:
                    draw_status(frame, self.status)
                    
                    # Convert color format from BGR (OpenCV) to RGB (PIL)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    
                    # Create CTkImage and update label
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(380, 240))
                    self.cam_label.configure(image=ctk_img, text="")
            
            # Schedule the next frame update in 15ms (even if ret is False)
            self.after(15, self.update_camera)
        else:
            self._loop_active = False

    def ensure_camera_active(self):
        """Helper to ensure camera is opened and loop is running."""
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        
        if not getattr(self, "_loop_active", False):
            self.update_camera()

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
