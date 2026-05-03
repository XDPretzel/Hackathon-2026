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
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                import comtypes
                
                # Ensure COM is initialized for this thread
                try:
                    comtypes.CoInitialize()
                except:
                    pass
                    
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
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
                try:
                    # pycaw returns a scalar 0.0 to 1.0
                    return int(self.volume.GetMasterVolumeLevelScalar() * 100)
                except Exception as e:
                    print(f"DEBUG: pycaw get_volume failed: {e}")
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
                try:
                    self.volume.SetMasterVolumeLevelScalar(volume_level / 100.0, None)
                except Exception as e:
                    print(f"DEBUG: pycaw set_volume failed: {e}")
                    # Fallback to keys if pycaw fails during operation
                    if volume_level > self.get_system_volume():
                        pyautogui.press('volumeup')
                    elif volume_level < self.get_system_volume():
                        pyautogui.press('volumedown')
            else:
                # If pycaw is not available at all, try to use media keys
                # We can't set absolute volume, so we just nudge it
                if volume_level > 50:
                    pyautogui.press('volumeup')
                else:
                    pyautogui.press('volumedown')

    def _mac_media_key(self, key_code):
        try:
            import AppKit
            import Quartz
            NX_SYSDEFINED = 14
            def doKey(down):
                ev = AppKit.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    NX_SYSDEFINED, (0, 0), 0xa00 if down else 0xb00, 0, 0, None, 8,
                    (key_code << 16) | ((0xa if down else 0xb) << 8), -1
                )
                Quartz.CGEventPost(0, ev.CGEvent())
            doKey(True)
            doKey(False)
        except Exception as e:
            print(f"Failed to send Mac media key: {e}")

    # --- Media Target Detection ---
    def get_active_media_target(self):
        """Returns 'youtube' if YouTube is active in Chrome, otherwise 'spotify'"""
        if self.is_mac:
            try:
                cmd_chrome = "osascript -e 'tell application \"System Events\" to count (every process whose name is \"Google Chrome\")'"
                if int(subprocess.check_output(cmd_chrome, shell=True).decode().strip()) > 0:
                    cmd_url = "osascript -e 'tell application \"Google Chrome\" to get URL of active tab of front window'"
                    url = subprocess.check_output(cmd_url, shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    if "youtube.com/watch" in url:
                        return "youtube"
            except:
                pass
        return "spotify"

    # --- Media Controls ---
    def skip_track(self):
        target = self.get_active_media_target()
        if self.is_mac:
            if target == "youtube":
                # Shift+N skips to the next video on YouTube (Requires Chrome to be focused)
                subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"Google Chrome\" to keystroke \"N\" using shift down'", shell=True)
            else:
                self._mac_media_key(17) # NX_KEYTYPE_NEXT
        else:
            pyautogui.press('nexttrack')

    def previous_track(self):
        target = self.get_active_media_target()
        if self.is_mac:
            if target == "youtube":
                # Shift+P goes to the previous video on YouTube
                subprocess.run("osascript -e 'tell application \"System Events\" to tell process \"Google Chrome\" to keystroke \"P\" using shift down'", shell=True)
            else:
                self._mac_media_key(18) # NX_KEYTYPE_PREVIOUS
        else:
            pyautogui.press('prevtrack')

    def toggle_play_pause(self):
        if self.is_mac:
            self._mac_media_key(16) # NX_KEYTYPE_PLAY
        else:
            pyautogui.press('playpause')

    def play(self):
        if self.is_mac:
            self._mac_media_key(16)
        else:
            pyautogui.press('playpause')

    def pause(self):
        if self.is_mac:
            self._mac_media_key(16)
        else:
            pyautogui.press('playpause')

    def get_spotify_state(self):
        # We can no longer reliably get the state of global media
        return "unknown"
