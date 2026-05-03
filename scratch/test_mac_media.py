import subprocess
import platform
import time
from system_controller import SystemController

def test_mac_media_v2():
    if platform.system() != 'Darwin':
        print("Not on Mac")
        return

    sc = SystemController()
    
    print(f"Current OS: {platform.system()} {platform.release()}")
    print(f"Detected Target: {sc.get_active_media_target()}")
    
    print("\n1. Testing Volume (Absolute set to 40)")
    sc.set_system_volume(40)
    time.sleep(1)
    new_vol = sc.get_system_volume()
    print(f"Volume is now: {new_vol}")

    print("\n2. Testing Play/Pause")
    print("If you have YouTube open, it should toggle. If not, it will try Spotify/Music.")
    sc.toggle_play_pause()
    print("Play/Pause command sent.")

    print("\n3. Testing Skip (Next)")
    sc.skip_track()
    print("Skip command sent.")

if __name__ == "__main__":
    test_mac_media_v2()
