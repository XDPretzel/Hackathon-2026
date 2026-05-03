#========= UI and Background Tray Process =========
import customtkinter as ctk # modern gui library
import sys
import traceback
import os

# Redirect errors to a log file for debugging bundled app
log_path = os.path.join(os.path.expanduser("~"), "gest_crash_log.txt")
sys.stderr = open(log_path, "w")
sys.stdout = open(os.path.join(os.path.expanduser("~"), "gest_output_log.txt"), "w")

try:
    from ui_utils import draw_status, draw_volume_bar # custom ui overlay utilities
    import threading # for running the background system tray process
    from PIL import Image, ImageDraw # image processing for camera and tray icons
    import pystray # system tray/menu bar integration

    #====== Computer Vision and Timing =========
    import cv2 # opencv for webcam capture and frame processing
    import time # timing for cooldowns and gesture settle delays
    import mediapipe as mp

    #========== System Operations 
    import subprocess # to run apple script / system commands for media control
    import pyautogui # simulating keypresses and keyboard shortcuts
    from system_controller import SystemController # native macos/windows media control bridge

    #====== Our Gesture Detection Logic ========
    from gesture_detector import ( # custom gesture recognition logic
        play_gesture, pause_gesture, skip_gesture, previous_gesture, 
        is_pinching, get_hand_y, get_hand_x
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

    #==============================================================================
    # Main Application Class
    #==============================================================================
    class App(ctk.CTk):
        """
        The core controller for the Gest application.
        It manages the UI, the camera lifecycle, hand tracking logic, 
        and system tray integration.
        """
        def __init__(self):
            super().__init__()
            self.title("Gest")
            # Initialize window size and style
            self.geometry("380x360")
            self.configure(fg_color="#0a0a0a")  # Deep onyx

            # Application State
            self.is_tracking = False
            self.is_camera_on = False
            self.minimize_to_tray = False 
            self.tray_icon = None
            self.cap = None     # Open Camera capture object

            # Logic Gesture State
            self.sys_ctrl = SystemController()
            self.COOLDOWN = 0.8
            
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

            #====== UI CompontetLAYOUT
            
            # Header Area
            self.header = ctk.CTkFrame(self, fg_color="transparent")
            self.header.pack(fill="x", padx=30, pady=(30, 10))
            
            # Logo and Title
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "gest.png")
                # For bundled app path
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(sys._MEIPASS, "gest.png")
                
                logo_img = Image.open(logo_path).convert("RGBA")
                # Extract alpha channel and create a white version
                alpha = logo_img.getchannel('A')
                white_logo = Image.new("RGBA", logo_img.size, (255, 255, 255, 255))
                white_logo.putalpha(alpha)
                
                logo_ctk = ctk.CTkImage(white_logo, size=(30, 30))
                self.logo_label = ctk.CTkLabel(self.header, image=logo_ctk, text="")
                self.logo_label.pack(side="left", padx=(0, 10))
            except:
                pass

            self.title_label = ctk.CTkLabel(self.header, text="GEST", font=("Segoe UI", 24, "bold"), text_color="#ffffff")
            self.title_label.pack(side="left")

            # Main Interaction Area (Power Button & Status)
            self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.content_frame.pack(fill="both", expand=True, padx=30)

            # Video Preview (Stylized)
            self.cam_container = ctk.CTkFrame(self.content_frame, fg_color="#121212", corner_radius=20, border_width=1, border_color="#222222")
            self.cam_label = ctk.CTkLabel(self.cam_container, text="CAMERA INACTIVE", font=("Segoe UI", 10), text_color="#444444")
            self.cam_label.pack(fill="both", expand=True, padx=2, pady=2)
            
            # Central Control Group
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

            # Nav Bar
            self.bottom_bar = ctk.CTkFrame(self, fg_color="#0f0f0f", height=60, corner_radius=0)
            self.bottom_bar.pack(fill="x", side="bottom")
            self.cam_toggle_btn = ctk.CTkButton(self.bottom_bar, text="VIEW FEED", font=("Segoe UI", 11, "bold"),
                                                fg_color="transparent", hover_color="#181818", text_color="#888888",
                                                command=self.toggle_camera)
            self.cam_toggle_btn.pack(side="left", padx=20, pady=10)
            self.minimize_btn = ctk.CTkButton(self.bottom_bar, text="EXIT", font=("Segoe UI", 11, "bold"),
                                               fg_color="transparent", hover_color="#181818", text_color="#888888",
                                               command=self.on_close)
            self.minimize_btn.pack(side="right", padx=20)

            self.perm_btn = ctk.CTkButton(self.bottom_bar, text="?", width=30, font=("Segoe UI", 11, "bold"),
                                          fg_color="transparent", hover_color="#181818", text_color="#444444",
                                          command=self.request_permissions)
            self.perm_btn.pack(side="right", padx=5)

            # Handle Close Event
            self.protocol('WM_DELETE_WINDOW', self.on_close)
            
            # Auto-start tracking when the app opens
            self.after(500, self.toggle_tracking)

        #==============================================================================
        # POWER AND TRACKING CONTROL
        #==============================================================================
        def toggle_tracking(self):
            """Switches the AI processing loop ON or OFF."""
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
                if not self.is_camera_on and self.cap:
                    self.cap.release()
                    self.cap = None

        def toggle_camera(self):
            """Toggles the visibility of the camera feed in the main window."""
            self.is_camera_on = not self.is_camera_on
            if self.is_camera_on:
                self.geometry("380x420")
                self.cam_toggle_btn.configure(text="← BACK", text_color="#ffffff")
                self.button_container.pack_forget()
                self.cam_container.pack(fill="x", pady=(0, 20))
                self.ensure_camera_active()
            else:
                self.geometry("380x340")
                self.cam_toggle_btn.configure(text="VIEW FEED", text_color="#888888")
                self.cam_container.pack_forget()
                self.button_container.pack(expand=True)
                
                # Stop OpenCV camera only if tracking is also off
                if not self.is_tracking and self.cap:
                    self.cap.release()
                    self.cap = None

        #==============================================================================
        # THE CORE PROCESSING LOOP
        #==============================================================================
        def update_camera(self):
            """
            The main event loop. This runs continuously to:
            1. Capture frames from the camera.
            2. Feed them into MediaPipe to find hand landmarks.
            3. Match landmarks against known gestures (Pinch, Palm, Fist).
            4. Trigger system actions via SystemController.
            """
            if (self.is_camera_on or self.is_tracking) and self.cap and self.cap.isOpened():
                self._loop_active = True
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.flip(frame, 1)  # flipping image so gestures feel natural
                    
                    if self.is_tracking:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = hands.process(rgb_frame)
                        current_time = time.time()

                        if results.multi_hand_landmarks:
                            for hand_landmarks in results.multi_hand_landmarks:
                                if self.is_camera_on:
                                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                                # --- VOLUME CONTROL (Pitch) ---
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
                                        
                                        # Asymmetric sensitivity: Back swipe is less sensitive (0.4 vs 0.25)
                                        is_skip = delta_x > self.SWIPE_THRESHOLD
                                        is_prev = delta_x < -self.SWIPE_THRESHOLD

                                        # Trigger Skip (Right) or Previous (Left)
                                        if is_skip or is_prev:
                                            if current_time - self.last_action_time > self.COOLDOWN:
                                                if is_skip:
                                                    print("DEBUG: Triggering Skip Track")
                                                    self.sys_ctrl.skip_track()
                                                    self.status = "SKIPPING >>"
                                                    self.last_action_time = current_time
                                                    self.swipe_start_x = current_x 
                                                elif is_prev and (current_time - self.palm_start_time > 0.4):
                                                    print("DEBUG: Triggering Previous Track")
                                                    self.sys_ctrl.previous_track()
                                                    self.status = "<< PREVIOUS"
                                                    self.last_action_time = current_time
                                                    self.swipe_start_x = current_x 
                                        
                                        # Also check for "Play" while holding palm
                                        elif current_time - self.last_action_time > self.COOLDOWN:
                                            spotify_state = self.sys_ctrl.get_spotify_state()
                                            # If state is unknown, always attempt to play (or toggle)
                                            if spotify_state == "paused" or spotify_state == "unknown":
                                                print("DEBUG: Triggering Play")
                                                self.sys_ctrl.play()
                                                self.status = "RESUMING..."
                                                self.win_is_playing = True
                                                self.last_action_time = current_time
                                    else:
                                        self.status = "PREPARING PALM..."
                                
                                # --- 3. PAUSE GESTURE (Closed Fist) ---
                                elif pause_gesture(hand_landmarks):
                                    self.palm_start_time = 0
                                    self.is_swiping = False
                                    self.swipe_start_x = None
                                    
                                    if current_time - self.last_action_time > self.COOLDOWN:
                                        spotify_state = self.sys_ctrl.get_spotify_state()
                                        # If state is unknown, always attempt to pause
                                        if spotify_state == "playing" or spotify_state == "unknown":
                                            print("DEBUG: Triggering Pause")
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

                    if self.is_camera_on:
                        draw_status(frame, self.status)
                        
                        # Convert color format from BGR (OpenCV) to RGB (PIL)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        
                        # Create CTkImage and update label
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(380, 240))
                        self.cam_label.configure(image=ctk_img, text="")
                
                # Loop recursively using tkinter's .after() to prevent blocking the UI thread
                self.after(15, self.update_camera)
            else:
                self._loop_active = False

        def ensure_camera_active(self):
            """Helper to ensure camera is opened and loop is running."""
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            if not getattr(self, "_loop_active", False):
                self.update_camera()

        #==============================================================================
        # SYSTEM TRAY AND WINDOW LIFECYCLE
        #==============================================================================
        def on_close(self):
            """Handles what happens when the window is closed or minimized."""
            if self.minimize_to_tray:
                # Re-release camera ONLY if tracking is also OFF
                if not self.is_tracking and self.cap:
                    self.cap.release()
                    self.cap = None
                self.withdraw()     # hide window
                self.start_tray()
            else:
                if self.cap:
                    self.cap.release()
                self.quit()

        def start_tray(self):
            """Creates and runs the menu bar icon."""
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
            """Restores the window from the system tray."""
            self.tray_icon.stop()
            self.after(0, self.deiconify)
            # If camera was supposed to be on, ensure cap is active
            if self.is_camera_on or self.is_tracking:
                self.after(100, self.reinit_camera)

        def reinit_camera(self):
            """Re-establishes camera connection if it was released while in tray."""
            if (self.is_camera_on or self.is_tracking) and not self.cap:
                self.cap = cv2.VideoCapture(0)
                self.update_camera()

        def quit_app(self, icon, item):
            """Completely terminates the application."""
            self.tray_icon.stop()
            if self.cap:
                self.cap.release()
            self.quit()

        def request_permissions(self):
            """Triggers system prompts for Accessibility and Automation."""
            self.status = "CHECKING PERMS..."
            self.status_label.configure(text=self.status)
            
            # This osascript command triggers the 'Automation' permission prompt for Chrome
            # and 'Accessibility' prompt for System Events.
            cmd = "osascript -e 'tell application \"Google Chrome\" to get URL of active tab of front window'"
            try:
                subprocess.run(cmd, shell=True, capture_output=True)
                self.status = "PERMS REQUESTED"
            except:
                self.status = "PERMS FAILED"
            
            # Also try to trigger Accessibility by using System Events
            cmd_sys = "osascript -e 'tell application \"System Events\" to get name of first process'"
            try:
                subprocess.run(cmd_sys, shell=True, capture_output=True)
            except:
                pass
            
            self.status_label.configure(text=self.status)

    if __name__ == "__main__":
        try:
            App().mainloop()
        except Exception as e:
            with open(log_path, "a") as f:
                f.write("\n--- CRASH AT RUNTIME ---\n")
                traceback.print_exc(file=f)

except Exception as e:
    with open(log_path, "a") as f:
        f.write("\n--- CRASH DURING INITIALIZATION ---\n")
        traceback.print_exc(file=f)
