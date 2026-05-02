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
