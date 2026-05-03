import os
import subprocess
from PIL import Image

def create_icns(png_path, icns_path):
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found")
        return False
    
    # Create a white version of the PNG for the icon
    img = Image.open(png_path).convert("RGBA")
    alpha = img.getchannel('A')
    white_img = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_img.putalpha(alpha)
    
    temp_white_png = "gest_white_temp.png"
    white_img.save(temp_white_png)
    
    iconset_path = "Gest.iconset"
    os.makedirs(iconset_path, exist_ok=True)
    
    # Standard icon sizes
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    for size in sizes:
        # Normal
        out = os.path.join(iconset_path, f"icon_{size}x{size}.png")
        subprocess.run(["sips", "-z", str(size), str(size), temp_white_png, "--out", out], capture_output=True)
        
        # Retina
        if size * 2 <= 1024:
            out_retina = os.path.join(iconset_path, f"icon_{size}x{size}@2x.png")
            subprocess.run(["sips", "-z", str(size*2), str(size*2), temp_white_png, "--out", out_retina], capture_output=True)
            
    # Convert iconset to icns
    subprocess.run(["iconutil", "-c", "icns", iconset_path, "-o", icns_path])
    
    # Cleanup
    import shutil
    shutil.rmtree(iconset_path)
    if os.path.exists(temp_white_png):
        os.remove(temp_white_png)
    return True

if __name__ == "__main__":
    if create_icns("gest.png", "Gest.icns"):
        print("Successfully created White Gest.icns")
