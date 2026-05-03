tell application "System Events"
    set activeApp to name of first application process whose frontmost is true
end tell
tell application "Google Chrome" to activate
delay 0.1
tell application "System Events" to keystroke "k"
tell application activeApp to activate
