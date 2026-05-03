import cv2

def draw_status(frame, status_text):
    """
    Draws a green status message in the bottom-right corner of the frame.
    """
    if not status_text:
        return
    
    # Get frame dimensions
    height, width, _ = frame.shape
    
    # Text settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2
    color = (0, 255, 0)  # Green in BGR
    
    # Get text size to position it correctly from the right edge
    text_size = cv2.getTextSize(status_text, font, font_scale, font_thickness)[0]
    
    # Calculate position (Bottom Right with 20px padding)
    text_x = width - text_size[0] - 20
    text_y = height - 20
    
    # Draw the text
    cv2.putText(frame, status_text, (text_x, text_y), font, font_scale, color, font_thickness, cv2.LINE_AA)

def draw_volume_bar(frame, volume_level):
    """
    Draws a vertical volume bar on the left side of the frame.
    volume_level should be between 0 and 100.
    """
    height, width, _ = frame.shape
    
    # Bar settings
    bar_x = 30
    bar_y_start = int(height * 0.2)
    bar_y_end = int(height * 0.8)
    bar_height = bar_y_end - bar_y_start
    bar_width = 20
    
    # Draw the background of the bar (Empty)
    cv2.rectangle(frame, (bar_x, bar_y_start), (bar_x + bar_width, bar_y_end), (100, 100, 100), -1)
    
    # Calculate fill height
    fill_height = int((volume_level / 100) * bar_height)
    fill_y_start = bar_y_end - fill_height
    
    # Draw the filled part (Green)
    cv2.rectangle(frame, (bar_x, fill_y_start), (bar_x + bar_width, bar_y_end), (0, 255, 0), -1)
    
    # Add a "VOL" label
    cv2.putText(frame, f"{int(volume_level)}%", (bar_x - 10, bar_y_start - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
