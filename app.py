import os
import cv2
from flask import Flask,url_for, redirect,render_template, Response, jsonify, request, stream_with_context, make_response

from deepface import DeepFace
import threading
import time
import logging
import pandas as pd
from io import StringIO
import datetime
import json
import google.generativeai as genai # Import Gemini library
from io import BytesIO
import firebase_admin 
from firebase_admin import credentials, auth

from functools import wraps
 


# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- Configuration ---
# IMPORTANT: Replace with your actual Gemini API key
# Consider using environment variables for security: os.environ.get('GEMINI_API_KEY')
GEMINI_API_KEY = "your key"
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash') # Or choose a specific model
    app.logger.info("Gemini AI configured successfully.")
except Exception as e:
    app.logger.error(f"Failed to configure Gemini AI: {e}. Analysis endpoint will not work.")
    gemini_model = None # Ensure model is None if configuration fails

# --- Global Variables ---
capture = None # OpenCV video capture object
video_thread = None
analysis_data = [] # List to store analysis results ({timestamp, emotion, dominant_emotion})
behavior_analysis_history = [] # Stores text analyses from Gemini
analysis_lock = threading.Lock()
is_processing = False # Flag to indicate if analysis is running
frame_skip = 5 # Analyze every Nth frame to reduce load
last_frame_analyzed = None # Store the latest analyzed frame for display (optional)
# --- Constants for Gemini Analysis ---
GEMINI_ANALYSIS_INTERVAL_SECONDS = 15 # How often to call Gemini API
GEMINI_DATA_WINDOW_SECONDS = 60 # How much past data to send to Gemini

# --- Helper Functions ---
def ensure_dir(directory):
    """Ensures a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

# --- LLM Integration (Placeholder) ---
def get_behavioral_analysis_from_gemini(data_batch):
    """
    Sends a batch of emotion data to Gemini and returns its textual analysis.
    Replace this placeholder with actual Gemini API call.
    """
    if not gemini_model or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        app.logger.warning("Gemini model not configured or API key missing. Skipping analysis.")
        return "(Gemini analysis skipped - API key or configuration missing)"

    if not data_batch:
        return "(Not enough data yet for analysis)"

    # 1. Format the data (example: create a summary string or keep as structured list)
    # Example: Convert timestamps to relative time, summarize dominant emotions
    formatted_data_str = "Recent emotion readings:\n"
    try:
        for entry in data_batch[-10:]: # Send last 10 entries as example
            ts = datetime.datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
            formatted_data_str += f"- Time: {ts}, Dominant Emotion: {entry['dominant_emotion']}\n"
            # Optionally include full emotion scores if useful
            # formatted_data_str += f"  Scores: {json.dumps(entry['emotions'])}\n"

        # 2. Craft the prompt
        prompt = f"""
        You are an expert behavioral analyst assisting in a suspect interrogation.
        Analyze the following sequence of dominant emotions detected from the suspect's facial expressions.
        Provide a brief (1-2 sentences) behavioral analysis focusing on potential stress, deception indicators, or significant emotional shifts.
        Do not repeat the raw data in your analysis. Be concise.

        Recent Emotion Data:
        {formatted_data_str}

        Analysis:
        """
        app.logger.info(f"Sending prompt to Gemini (sample data length: {len(data_batch)} entries).")
        app.logger.debug(f"Gemini Prompt (first 100 chars): {prompt[:100]}...")

        # 3. Call the Gemini API
        # IMPORTANT: Replace this section with the actual SDK call
        # Handle potential API errors (rate limits, connection issues, etc.)
        try:
            response = gemini_model.generate_content(prompt)
            analysis_text = response.text
            app.logger.info("Received analysis from Gemini.")
            app.logger.debug(f"Gemini Response: {analysis_text}")
            return analysis_text
        except Exception as e:
            app.logger.error(f"Error calling Gemini API: {e}")
            return f"(Error during Gemini analysis: {e})"

    except Exception as e:
         app.logger.error(f"Error formatting data or prompt for Gemini: {e}")
         return "(Error preparing data for Gemini)"

# --- Video Capture and Analysis Thread ---
def capture_and_analyze():
    """
    Captures video frames, performs emotion analysis, and stores results.
    Runs in a separate thread.
    """
    global capture, analysis_data, is_processing, last_frame_analyzed
    app.logger.info("Starting video capture thread...")

    potential_indices = [0, 1, -1]
    for index in potential_indices:
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            app.logger.info(f"Webcam opened successfully at index {index}.")
            break
        else:
            capture.release()
            capture = None
            app.logger.warning(f"Failed to open webcam at index {index}.")

    if not capture or not capture.isOpened():
        app.logger.error("Cannot open webcam on any common index.")
        is_processing = False
        return

    frame_count = 0
    while is_processing:
        ret, frame = capture.read()
        if not ret:
            app.logger.warning("Failed to grab frame, stopping.")
            break

        frame_count += 1
        if frame_count % frame_skip == 0: # Process every Nth frame
            try:
                # DeepFace expects BGR, OpenCV provides BGR by default
                results = DeepFace.analyze(
                    frame,
                    actions=['emotion'],
                    enforce_detection=True, # Only analyze if face detected
                    silent=True # Suppress verbose console output
                )

                # DeepFace returns a list of dicts, one per face
                # We'll focus on the first detected face for simplicity
                if results and isinstance(results, list):
                    first_face_result = results[0]
                    dominant_emotion = first_face_result.get('dominant_emotion')
                    emotions = first_face_result.get('emotion')
                    timestamp = datetime.datetime.now().isoformat()

                    new_data_point = {
                        "timestamp": timestamp,
                        "dominant_emotion": dominant_emotion,
                        "emotions": emotions # Store all emotion scores
                    }
                    with analysis_lock:
                        analysis_data.append(new_data_point)
                    app.logger.debug(f"Analysis @ {timestamp}: {dominant_emotion}")
                    last_frame_analyzed = frame # Update last analyzed frame (optional)

            except ValueError as e:
                if "Face could not be detected" in str(e):
                    app.logger.debug("No face detected in frame.")
                    # Optionally store a 'no face' event
                    # with analysis_lock:
                    #     analysis_data.append({
                    #         "timestamp": datetime.datetime.now().isoformat(),
                    #         "dominant_emotion": "No Face",
                    #         "emotions": {}
                    #     })
                else:
                    app.logger.error(f"Error during DeepFace analysis: {e}")
            except Exception as e:
                app.logger.error(f"Unexpected error in analysis loop: {e}")

        # Optional: Reduce loop speed slightly if needed
        # time.sleep(0.01)

    # Release webcam and clean up when stopping
    if capture:
        capture.release()
    capture = None
    app.logger.info("Video capture thread stopped.")


# --- Server-Sent Events Stream ---
def generate_analysis_stream():
    """Streams emotion updates and periodic behavioral analysis using SSE."""
    global analysis_data, behavior_analysis_history
    last_emotion_sent_index = -1
    last_gemini_analysis_time = time.time()

    try:
        while True:
            now = time.time()
            new_emotion_data_to_send = []
            current_analysis_batch = []

            with analysis_lock:
                # 1. Send any new individual emotion updates for the chart
                current_length = len(analysis_data)
                if current_length > last_emotion_sent_index + 1:
                    new_emotion_data_to_send = analysis_data[last_emotion_sent_index + 1:]
                    last_emotion_sent_index = current_length - 1

                # 2. Check if it's time for Gemini analysis
                if now - last_gemini_analysis_time >= GEMINI_ANALYSIS_INTERVAL_SECONDS:
                    # Prepare data batch (e.g., last N seconds)
                    cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=GEMINI_DATA_WINDOW_SECONDS)
                    current_analysis_batch = [d for d in analysis_data if datetime.datetime.fromisoformat(d['timestamp']) >= cutoff_time]
                    last_gemini_analysis_time = now # Reset timer even if batch is empty

            # Yield new emotion data (outside the lock)
            for data_point in new_emotion_data_to_send:
                # Add message type field
                sse_data = {"type": "emotion_update", "payload": data_point}
                json_data = json.dumps(sse_data)
                app.logger.debug(f"SERVER SENDING SSE: {json_data}")
                yield f"data: {json_data}\r\n\r\n"

            # Perform Gemini analysis and yield result (outside the lock)
            if current_analysis_batch:
                app.logger.info(f"Triggering Gemini analysis for batch size: {len(current_analysis_batch)}")
                analysis_text = get_behavioral_analysis_from_gemini(current_analysis_batch)
                with analysis_lock:
                    behavior_analysis_history.append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "analysis": analysis_text
                    })
                # Send the new analysis text
                sse_data = {"type": "behavior_analysis", "payload": analysis_text}
                json_data = json.dumps(sse_data)
                app.logger.debug(f"SERVER SENDING SSE: {json_data}")
                yield f"data: {json_data}\r\n\r\n"

            # Wait before next check
            time.sleep(0.5)

    except GeneratorExit:
        app.logger.info("SSE client disconnected.")
    finally:
        app.logger.info("Stopped sending SSE data.")

# firebase lets initialize 
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            decoded_token = auth.verify_id_token(token)
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorated

# --- Routes ---
# @app.route('/')
# def index():
#     """Serves the main HTML page."""
#     return render_template('index_realtime.html')  
@app.route('/')
def home():
    token = request.cookies.get('firebaseToken')
    if token:
        try:
            auth.verify_id_token(token)
            return redirect(url_for('index_realtime'))
        except:
            pass  # Invalid or expired token
    return redirect(url_for('login'))


@app.route('/index_realtime')
def index_realtime():
    # Check both cookie and Authorization header
    token = request.cookies.get('firebaseToken') or \
            request.headers.get('Authorization')
    
    if not token:
        app.logger.warning("No token found for /index_realtime")
        return redirect(url_for('login'))
    
    try:
        # Remove 'Bearer ' prefix if present
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        decoded_token = auth.verify_id_token(token)
        app.logger.debug("Token verified for /index_realtime")
        return render_template('index_realtime.html')
    except Exception as e:
        app.logger.error(f"Token verification failed for /index_realtime: {str(e)}")
        return redirect(url_for('login'))





# Auth Routes
@app.route('/auth/login')
def login():
    token = request.cookies.get('firebaseToken')
    if token:
        try:
            auth.verify_id_token(token)
            return redirect(url_for('index_realtime'))
        except:
            pass
    return render_template('auth/login.html')





@app.route('/auth/register')
def register():
    return render_template('auth/register.html')

@app.route('/auth/forgot')
def forgot_password():
    return render_template('auth/forgot.html')

@app.route('/auth/mfa')
def mfa_verify():
    return render_template('auth/mfa.html')

@app.route('/set_auth_cookie', methods=['POST'])
def set_auth_cookie():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token missing"}), 400

    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        auth.verify_id_token(token)
        response = make_response(jsonify({"message": "Token set"}))
        response.set_cookie('firebaseToken', token, httponly=True, max_age=3600)  # 1 hour expiry
        return response
    except Exception as e:
        app.logger.error(f"Token verification error: {str(e)}")
        return jsonify({"message": str(e)}), 403


    
# API Routes
@app.route('/api/check-auth')
def check_auth():
    return jsonify({'authenticated': True})

@app.route('/logout')
def logout():
    app.logger.info("Logout route called")
    response = make_response(redirect('/auth/login'))
    response.delete_cookie('firebaseToken')
    return response

# Updated token verification function
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('firebaseToken') or \
               request.headers.get('Authorization')
        
        if not token:
            app.logger.warning("No token found in request")
            return jsonify({'message': 'Token is missing!'}), 403
            
        # Remove 'Bearer ' prefix if present
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        try:
            app.logger.debug(f"Verifying token: {token[:10]}...")
            decoded_token = auth.verify_id_token(token)
            app.logger.debug("Token verified successfully")
        except Exception as e:
            app.logger.error(f"Token verification failed: {str(e)}")
            return jsonify({'message': f'Invalid token: {str(e)}'}), 403
            
        return f(*args, **kwargs)
    return decorated

@app.route('/protected')
def protected_route():
    token = request.cookies.get('firebaseToken')

    if not token:
        return jsonify({"message": "Token is missing!"}), 403

    try:
        decoded_token = auth.verify_id_token(token)
        # token is valid
        return render_template('index_realtime.html')
    except Exception as e:
        return jsonify({"message": f"Invalid token: {str(e)}"}), 403





 

    
@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Starts the video capture and analysis thread."""
    global video_thread, is_processing, analysis_data, behavior_analysis_history
    if is_processing:
        return jsonify({"status": "Already processing"}), 400

    app.logger.info("Received request to start analysis.")
    is_processing = True
    with analysis_lock:
        analysis_data = [] # Clear raw data
        behavior_analysis_history = [] # Clear previous analyses
    # Start the background thread
    video_thread = threading.Thread(target=capture_and_analyze, daemon=True)
    video_thread.start()
    return jsonify({"status": "Processing started"})

@app.route('/stop_analysis', methods=['POST'])
def stop_analysis():
    """Stops the video capture and analysis thread."""
    global video_thread, is_processing, capture
    if not is_processing:
        return jsonify({"status": "Not processing"}), 400

    app.logger.info("Received request to stop analysis.")
    is_processing = False # Signal the thread to stop

    # Wait for the thread to finish
    if video_thread and video_thread.is_alive():
        video_thread.join(timeout=5.0) # Wait up to 5 seconds
        if video_thread.is_alive():
             app.logger.warning("Video thread did not stop gracefully.")
             # Force release capture if thread hangs (use cautiously)
             if capture:
                 capture.release()
                 capture = None

    video_thread = None
    app.logger.info("Processing stopped.")
    return jsonify({"status": "Processing stopped"})

@app.route('/analysis_stream')
def analysis_stream():
    """Endpoint for the SSE stream."""
    if not is_processing:
         return Response("Analysis not started.", status=404)
    # stream_with_context ensures the request context is available in the generator
    return Response(stream_with_context(generate_analysis_stream()), mimetype='text/event-stream')

@app.route('/get_report_data', methods=['GET'])
def get_report_data():
    """Returns the collected analysis data as JSON."""
    # Report now includes both raw emotion data and Gemini analyses
    with analysis_lock:
        report_data = {
            "emotion_log": list(analysis_data),
            "behavioral_analyses": list(behavior_analysis_history)
        }
    return jsonify(report_data)

@app.route('/download_report')
def download_report():
    """Download the analysis report."""
    report_content = generate_report()
    
    # Create a response with the report content
    response = make_response(report_content)
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = "attachment; filename=interrogation_report.txt"
    
    return response

def generate_report():
    """Generate a comprehensive report of the analysis session."""
    if not analysis_data:
        return "No analysis data available."

    report = []
    report.append("=== Interrogation Analysis Report ===\n")
    
    # Session Information
    report.append("Session Information:")
    if len(analysis_data) > 0:
        start_time = analysis_data[0].get('timestamp', 'N/A')
        end_time = analysis_data[-1].get('timestamp', 'N/A')
        report.append(f"Start Time: {start_time}")
        report.append(f"End Time: {end_time}")
        # Calculate duration if we have valid timestamps
        try:
            start_dt = datetime.datetime.fromisoformat(start_time)
            end_dt = datetime.datetime.fromisoformat(end_time)
            duration = end_dt - start_dt
            report.append(f"Duration: {duration}")
        except:
            report.append("Duration: N/A")
    else:
        report.append("Start Time: N/A")
        report.append("End Time: N/A")
        report.append("Duration: N/A")
    report.append("")
    
    # Emotion Analysis Summary
    report.append("Emotion Analysis Summary:")
    report.append("------------------------")
    
    # Calculate emotion statistics
    emotion_stats = {}
    for entry in analysis_data:
        emotions = entry.get('emotions', {})
        for emotion, value in emotions.items():
            if emotion not in emotion_stats:
                emotion_stats[emotion] = []
            emotion_stats[emotion].append(value)
    
    # Add emotion statistics to report
    for emotion, values in emotion_stats.items():
        if values:
            avg = sum(values) / len(values)
            max_val = max(values)
            min_val = min(values)
            report.append(f"{emotion.capitalize()}:")
            report.append(f"  Average: {avg:.2f}%")
            report.append(f"  Maximum: {max_val:.2f}%")
            report.append(f"  Minimum: {min_val:.2f}%")
    
    # Dominant Emotions Timeline
    report.append("\nDominant Emotions Timeline:")
    report.append("-------------------------")
    for entry in analysis_data:
        timestamp = entry.get('timestamp', 'N/A')
        dominant = entry.get('dominant_emotion', 'N/A')
        confidence = entry.get('confidence', 'N/A')
        report.append(f"Time: {timestamp}")
        report.append(f"Dominant Emotion: {dominant}")
        # Handle confidence value that could be string or float
        if isinstance(confidence, (int, float)):
            report.append(f"Confidence: {confidence:.2f}%")
        else:
            report.append(f"Confidence: {confidence}")
        report.append("---")
    
    # Behavioral Analysis
    report.append("\nBehavioral Analysis:")
    report.append("-------------------")
    for entry in behavior_analysis_history:
        timestamp = entry.get('timestamp', 'N/A')
        analysis = entry.get('analysis', 'N/A')
        report.append(f"Time: {timestamp}")
        report.append(f"Analysis: {analysis}")
        report.append("---")
    
    # Raw Data Summary
    report.append("\nRaw Data Summary:")
    report.append("----------------")
    report.append(f"Total Entries: {len(analysis_data)}")
    
    # Additional Notes
    report.append("\nAdditional Notes:")
    report.append("----------------")
    report.append("1. All emotion values are percentages (0-100)")
    report.append("2. Timestamps are in local time")
    report.append("3. Confidence scores indicate the reliability of emotion detection")
    report.append("4. Behavioral analysis is generated using Google's Gemini AI")
    
    return "\n".join(report)

# Optional route to display the latest analyzed frame (demonstration)
# @app.route('/video_display')
# def video_display():
#     def generate_frames():
#         global last_frame_analyzed
#         while True:
#             if last_frame_analyzed is not None:
#                 try:
#                     ret, buffer = cv2.imencode('.jpg', last_frame_analyzed)
#                     if ret:
#                         frame_bytes = buffer.tobytes()
#                         yield (b'--frame\\r\\n'
#                                b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame_bytes + b'\\r\\n')
#                 except Exception as e:
#                     app.logger.error(f"Error encoding frame: {e}")
#             time.sleep(0.1) # Adjust frame rate for display
#
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Session Management Routes ---
@app.route('/save_session', methods=['POST'])
def save_session():
    """Save the current analysis session to a file."""
    try:
        with analysis_lock:
            if not analysis_data:
                return jsonify({"status": "error", "error": "No data to save"}), 400
            
            # Create sessions directory if it doesn't exist
            sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
            ensure_dir(sessions_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
            filepath = os.path.join(sessions_dir, filename)
            
            # Prepare session data
            session_data = {
                "emotion_data": analysis_data,
                "behavior_analysis": behavior_analysis_history,
                "metadata": {
                    "timestamp": timestamp,
                    "total_emotions": len(analysis_data),
                    "total_analyses": len(behavior_analysis_history)
                }
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return jsonify({
                "status": "success",
                "message": "Session saved successfully",
                "filename": filename
            })
            
    except Exception as e:
        app.logger.error(f"Error saving session: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/list_sessions', methods=['GET'])
def list_sessions():
    """List all saved analysis sessions."""
    try:
        sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        ensure_dir(sessions_dir)
        
        sessions = []
        for filename in os.listdir(sessions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(sessions_dir, filename)
                file_stat = os.stat(filepath)
                sessions.append({
                    "filename": filename,
                    "modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "size": file_stat.st_size
                })
        
        return jsonify(sessions)
        
    except Exception as e:
        app.logger.error(f"Error listing sessions: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/load_session', methods=['POST'])
def load_session():
    """Load a saved analysis session."""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({"status": "error", "error": "No filename provided"}), 400
            
        filename = data['filename']
        sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        filepath = os.path.join(sessions_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "error": "Session file not found"}), 404
            
        with open(filepath, 'r') as f:
            session_data = json.load(f)
            
        return jsonify({
            "status": "success",
            "data": session_data
        })
        
    except Exception as e:
        app.logger.error(f"Error loading session: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# --- Emotion Trends Analysis Route ---
@app.route('/get_emotion_trends', methods=['GET'])
def get_emotion_trends():
    """Analyze and return emotion trends from the current session."""
    try:
        with analysis_lock:
            if not analysis_data:
                return jsonify({"status": "error", "error": "No data available for analysis"}), 400
            
            # Calculate basic statistics
            total_emotions = len(analysis_data)
            unique_emotions = set(d['dominant_emotion'] for d in analysis_data)
            emotion_changes = sum(1 for i in range(1, len(analysis_data)) 
                                if analysis_data[i]['dominant_emotion'] != analysis_data[i-1]['dominant_emotion'])
            
            # Calculate emotion distribution
            emotion_distribution = {}
            for entry in analysis_data:
                emotion = entry['dominant_emotion']
                emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
            
            # Find most common emotion
            most_common_emotion = max(emotion_distribution.items(), key=lambda x: x[1])[0]
            
            # Calculate time-based statistics
            start_time = datetime.datetime.fromisoformat(analysis_data[0]['timestamp'])
            end_time = datetime.datetime.fromisoformat(analysis_data[-1]['timestamp'])
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            emotions_per_minute = total_emotions / duration_minutes if duration_minutes > 0 else 0
            
            # Calculate average emotion duration
            emotion_durations = []
            current_emotion = analysis_data[0]['dominant_emotion']
            current_start = start_time
            
            for entry in analysis_data[1:]:
                if entry['dominant_emotion'] != current_emotion:
                    current_end = datetime.datetime.fromisoformat(entry['timestamp'])
                    duration = (current_end - current_start).total_seconds()
                    emotion_durations.append(duration)
                    current_emotion = entry['dominant_emotion']
                    current_start = current_end
            
            # Add duration for the last emotion
            if emotion_durations:
                last_duration = (end_time - current_start).total_seconds()
                emotion_durations.append(last_duration)
            
            average_emotion_duration = sum(emotion_durations) / len(emotion_durations) if emotion_durations else 0
            
            # Calculate average confidence if available
            confidence_values = []
            for entry in analysis_data:
                if 'confidence' in entry:
                    try:
                        confidence_values.append(float(entry['confidence']))
                    except (ValueError, TypeError):
                        continue
            
            average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None
            
            trends = {
                "total_emotions": total_emotions,
                "unique_emotions": len(unique_emotions),
                "emotion_changes": emotion_changes,
                "most_common_emotion": most_common_emotion,
                "emotion_distribution": emotion_distribution,
                "time_based_stats": {
                    "emotions_per_minute": emotions_per_minute,
                    "average_emotion_duration": average_emotion_duration
                },
                "average_confidence": average_confidence
            }
            
            return jsonify({
                "status": "success",
                "trends": trends
            })
            
    except Exception as e:
        app.logger.error(f"Error analyzing emotion trends: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# --- Data Export Routes ---
@app.route('/export_csv', methods=['GET'])
def export_csv():
    """Export the current session data to CSV format."""
    try:
        with analysis_lock:
            if not analysis_data:
                return jsonify({"status": "error", "error": "No data to export"}), 400
            
            # Create a DataFrame from the emotion data
            df = pd.DataFrame(analysis_data)
            
            # Create a StringIO object to write the CSV data
            csv_data = StringIO()
            df.to_csv(csv_data, index=False)
            
            # Create the response
            response = make_response(csv_data.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=emotion_data.csv"
            response.headers["Content-type"] = "text/csv"
            
            return response
            
    except Exception as e:
        app.logger.error(f"Error exporting to CSV: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/export_excel', methods=['GET'])
def export_excel():
    """Export the current session data to Excel format."""
    try:
        with analysis_lock:
            if not analysis_data:
                return jsonify({"status": "error", "error": "No data to export"}), 400
            
            # Create a DataFrame from the emotion data
            df = pd.DataFrame(analysis_data)
            
            # Create a BytesIO object to write the Excel data
            excel_data = BytesIO()
            df.to_excel(excel_data, index=False)
            excel_data.seek(0)
            
            # Create the response
            response = make_response(excel_data.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=emotion_data.xlsx"
            response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            return response
            
    except Exception as e:
        app.logger.error(f"Error exporting to Excel: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    # Ensure necessary directories exist (though upload/db folders aren't used now)
    ensure_dir('database') # Keep if you plan DB features later
    # Important: Setting threaded=True is often necessary for handling concurrent requests
    # like the main page, SSE stream, and control actions. Use 'flask run' for development,
    # and a proper WSGI server (like Gunicorn with worker threads/processes) for production.
    app.run(debug=True, threaded=True, use_reloader=False) # use_reloader=False often needed with threads/webcam
