from flask import Flask, Response, request
import cv2
import numpy as np

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
        <body>
            <h1>Webcam Stream</h1>
            <img src="/video_feed" width="640" height="480"/>
        </body>
    </html>
    """

@app.route('/stream', methods=['POST'])
def stream():
    # Store the latest frame
    global current_frame
    frame_data = request.data
    nparr = np.frombuffer(frame_data, np.uint8)
    current_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return 'OK'

def generate_frames():
    while True:
        if 'current_frame' in globals():
            ret, buffer = cv2.imencode('.jpg', current_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=20807)
