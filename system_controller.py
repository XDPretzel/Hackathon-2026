import platform
import subprocess
import pyautogui

class SystemController:
    def __init__(self):
        self.os_name = platform.system()
        self.is_mac = self.os_name == 'Darwin'
        self.is_windows = self.os_name == 'Windows'
        
        if self.is_windows:
            try:
                from pycaw.pycaw import AudioUtilities
                
                devices = AudioUtilities.GetSpeakers()
                self.volume = devices.EndpointVolume
                self.has_pycaw = True
            except Exception as e:
                self.has_pycaw = False
                print(f"WARNING: pycaw initialization failed: {e}")
                print("Absolute volume control limited on Windows.")

    # --- Volume Controls ---
    def get_system_volume(self):
        if self.is_mac:
            try:
                cmd = "osascript -e 'output volume of (get volume settings)'"
                return int(subprocess.check_output(cmd, shell=True).decode().strip())
            except:
                return 50
        elif self.is_windows:
            if self.has_pycaw:
                # pycaw returns a scalar 0.0 to 1.0
                return int(self.volume.GetMasterVolumeLevelScalar() * 100)
            return 50 # Fallback
        return 50

    def set_system_volume(self, volume_level):
        volume_level = max(0, min(100, int(volume_level)))
        
        if self.is_mac:
            try:
                subprocess.run(f"osascript -e 'set volume output volume {volume_level}'", shell=True)
            except:
                pass
        elif self.is_windows:
            if self.has_pycaw:
                self.volume.SetMasterVolumeLevelScalar(volume_level / 100.0, None)

    # --- Media Controls ---
    def skip_track(self):
        if self.is_mac:
            subprocess.run("osascript -e 'tell application \"Spotify\" to next track'", shell=True)
        elif self.is_windows:
            pyautogui.press('nexttrack')

    def previous_track(self):
        if self.is_mac:
            subprocess.run("osascript -e 'tell application \"Spotify\" to previous track'", shell=True)
        elif self.is_windows:
            pyautogui.press('prevtrack')

    def toggle_play_pause(self):
        if self.is_mac:
            subprocess.run("osascript -e 'tell application \"Spotify\" to playpause'", shell=True)
        elif self.is_windows:
            pyautogui.press('playpause')

    def play(self):
        if self.is_mac:
            subprocess.run("osascript -e 'tell application \"Spotify\" to play'", shell=True)
        elif self.is_windows:
            # Windows media keys toggle 
            pyautogui.press('playpause')

    def pause(self):
        if self.is_mac:
            subprocess.run("osascript -e 'tell application \"Spotify\" to pause'", shell=True)
        elif self.is_windows:
           # Windows media keys toggle 
            pyautogui.press('playpause')

    def get_spotify_state(self):
        if self.is_mac:
            try:
                cmd = "osascript -e 'tell application \"Spotify\" to player state as string'"
                return subprocess.check_output(cmd, shell=True).decode().strip().lower()
            except:
                return "unknown"
        elif self.is_windows:
            #return "unknown" and rely on the toggle behavior
            return "unknown"
