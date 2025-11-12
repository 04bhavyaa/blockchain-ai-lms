import cv2
import mediapipe as mp
import time
import requests
import redis
import os
from flask import Flask, jsonify

app = Flask(__name__)

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize Redis connection
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

def calculate_attention_score(landmarks):
    """Calculate attention score based on eye landmarks"""
    if not landmarks:
        return 0.0
    
    # Get eye landmarks (simplified calculation)
    left_eye = landmarks[159]  # Left eye center
    right_eye = landmarks[386]  # Right eye center
    
    # Calculate eye openness (simplified)
    eye_openness = (left_eye.y + right_eye.y) / 2
    
    # Convert to attention score (0-1)
    attention_score = max(0, min(1, 1 - eye_openness))
    
    return attention_score

def track_attention():
    """Main attention tracking loop"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Starting attention tracking...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Calculate attention score
            attention_score = calculate_attention_score(landmarks)
            
            # Store in Redis
            redis_client.setex('attention_score', 30, str(attention_score))
            
            # Send to backend API
            try:
                requests.post(
                    f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/v1/attention/log/",
                    json={'score': attention_score, 'timestamp': time.time()},
                    timeout=1
                )
            except:
                pass  # Silently fail if backend is not available
            
            # Display on frame
            cv2.putText(frame, f"Attention: {attention_score:.2f}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display frame
        cv2.imshow('Attention Tracker', frame)
        
        # Break on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

@app.route('/status')
def status():
    """Get current attention status"""
    attention_score = redis_client.get('attention_score')
    if attention_score:
        return jsonify({
            'attention_score': float(attention_score),
            'status': 'tracking'
        })
    return jsonify({'status': 'not_tracking'})

@app.route('/start')
def start_tracking():
    """Start attention tracking"""
    # This would typically start the tracking in a separate thread
    return jsonify({'status': 'started'})

if __name__ == '__main__':
    # Start Flask app
    app.run(host='0.0.0.0', port=8002, debug=True) 