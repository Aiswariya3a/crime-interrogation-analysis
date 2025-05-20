# Crime Interrogation Analysis System

A sophisticated web application for analyzing facial expressions and behavioral patterns during crime interrogations. The system uses real-time video analysis, AI-powered behavioral insights, and secure authentication to provide comprehensive interrogation analysis tools.

## Features

- Real-time facial expression analysis using DeepFace
- AI-powered behavioral analysis using Google's Gemini AI
- Secure Firebase Authentication
- Live emotion tracking and visualization
- Session recording and playback
- Detailed analysis reports in text format
- User-specific case management
- System-wide interrogation records

## Prerequisites

- Python 3.8 or higher
- Webcam for video capture
- Firebase account
- Google Cloud account (for Gemini API)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd crime-interrogation-analysis
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Environment Setup

1. Create a `.env` file in the project root:

```bash
touch .env
```

2. Add the following environment variables to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-service-account.json
```

## Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication:

   - Go to Authentication > Sign-in method
   - Enable Email/Password authentication
   - (Optional) Enable other providers as needed

4. Get Firebase Admin SDK credentials:

   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely
   - Update `FIREBASE_CREDENTIALS_PATH` in `.env` to point to this file

5. Configure Firebase Web App:

   - Go to Project Settings > General
   - Scroll to "Your apps" section
   - Click the web icon (</>)
   - Register your app with a nickname
   - Copy the Firebase configuration object

6. Update Firebase configuration in your frontend code (typically in `static/js/firebase-config.js`):

```javascript
const firebaseConfig = {
  // Paste your Firebase config object here
};
```

## Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key
4. Add it to your `.env` file as `GEMINI_API_KEY`

## Running the Application

1. Ensure your virtual environment is activated
2. Start the Flask application:

```bash
python app.py
```

3. Access the application at `http://localhost:5000`

## Project Structure

```
crime-interrogation-analysis/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
└── user_cases.json      # Persistent storage for case data
```

## Dependencies

The project requires the following main dependencies:

- Flask
- OpenCV (cv2)
- DeepFace
- Firebase Admin SDK
- Google Generative AI (Gemini)
- Pandas
- Python-dotenv
