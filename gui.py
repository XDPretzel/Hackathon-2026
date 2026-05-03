import customtkinter as ctk
import threading
from PIL import Image, ImageDraw
import pystray
import cv2
from ui_utils import draw_status

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
        self.minimize_to_tray = True
        self.tray_icon = None
        self.cap = None

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

    def toggle_tracking(self):
        self.is_tracking = not self.is_tracking
        if self.is_tracking:
            self.power_btn.configure(fg_color="#00aa00", hover_color="#00cc00")
        else:
            self.power_btn.configure(fg_color="#333333", hover_color="#444444")

    def toggle_camera(self):
        self.is_camera_on = not self.is_camera_on
        if self.is_camera_on:
            self.cam_btn.configure(text="Hide Camera")
            self.cam_label.pack(after=self.power_btn, pady=20, fill="x", padx=20)
            
            # Start OpenCV camera
            self.cap = cv2.VideoCapture(0)
            self.update_camera()
        else:
            self.cam_btn.configure(text="Show Camera")
            self.cam_label.pack_forget()
            
            # Stop OpenCV camera
            if self.cap:
                self.cap.release()
                self.cap = None
            self.cam_label.configure(image=None, text="[Camera Feed]")

    def update_camera(self):
        if self.is_camera_on and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Optionally use our draw_status from camera_test
                status_text = "READY" if self.is_tracking else "IDLE"
                draw_status(frame, status_text)
                
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

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        if self.cap:
            self.cap.release()
        self.quit()

if __name__ == "__main__":
    App().mainloop()
