import PyInstaller.__main__
import os

# Run PyInstaller using the spec file
print("Starting build process using Gest.spec...")
PyInstaller.__main__.run([
    'Gest.spec',
    '--noconfirm',
    '--clean'
])

print("\nBuild complete! You can find the app in the 'dist/Gest' folder.")
