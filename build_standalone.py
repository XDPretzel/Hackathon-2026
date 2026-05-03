import PyInstaller.__main__
import os
import sys
import customtkinter
import mediapipe

# Get the path to customtkinter to include themes/assets
ctk_path = os.path.dirname(customtkinter.__file__)
mp_path = os.path.dirname(mediapipe.__file__)

# Define the build command
# --noconsole: Hide the terminal window on launch (GUI only)
# --onedir: Create a folder with the app (easier to debug)
# --name: Name of the application
# --add-data: Include customtkinter assets
params = [
    'main.py',
    '--noconsole',
    '--onedir',
    '--name=Gest',
    f'--add-data={ctk_path}{os.pathsep}customtkinter',
    f'--add-data={mp_path}{os.pathsep}mediapipe',
    '--clean',
    '--noconfirm',
]

# Run PyInstaller
print("Starting build process...")
PyInstaller.__main__.run(params)
print("\nBuild complete! You can find the app in the 'dist/Gest' folder.")
