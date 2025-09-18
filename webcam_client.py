import cv2
import requests
import numpy as np
from io import BytesIO
import time

def stream_webcam():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Encode frame to jpg
        _, img_encoded = cv2.imencode('.jpg', frame)
        
        try:
            # Send frame to server
            response = requests.post('http://157.66.255.8:20807/stream',
                                  data=img_encoded.tobytes(),
                                  headers={'Content-Type': 'image/jpeg'})
        except requests.exceptions.RequestException as e:
            print(f"Error sending frame: {e}")
            
        time.sleep(0.1)  # Limit frame rate
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()

if __name__ == '__main__':
    stream_webcam()
