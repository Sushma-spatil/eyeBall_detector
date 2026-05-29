# Real-Time Eye Tracking Web Application

A premium, modern web application that performs real-time eye tracking entirely in the browser using MediaPipe Face Mesh Iris landmarks.

## Features

- **Real-Time Iris Tracking:** Accurately tracks the center of both irises using MediaPipe's refined landmarks (indices 468-477).
- **Gaze Direction Detection:** Determines if the user is looking Left, Right, Up, Down, or Center.
- **Blink Detection:** Uses the Eye Aspect Ratio (EAR) to detect when the user blinks.
- **Premium SaaS UI:** Dark theme, glassmorphism elements, smooth animations, and a responsive layout.
- **Client-Side Processing:** All machine learning runs in the browser—no server needed, ensuring complete privacy.
- **Motion Interpolation:** Red tracking dots follow the eyes smoothly using Exponential Moving Average (EMA) smoothing.

## Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Libraries:** `@mediapipe/face_mesh`, `@mediapipe/camera_utils` (loaded via CDN)
- **Styling:** Custom CSS with Inter typography

## Setup Instructions

1. Clone or download this repository.
2. The application uses modern browser features (like Webcam access) which require a secure context (`https://` or `localhost`).
3. To run locally, serve the directory using a local web server. For example:
   - Using Python: `python -m http.server 8000`
   - Using Node.js: `npx serve .`
   - Or simply use the VS Code "Live Server" extension.
4. Open the provided local URL in your browser (e.g., `http://localhost:8000`).
5. Grant camera permissions when prompted.
6. The app will initialize the models and begin tracking.

## Usage

- Position yourself directly in front of the webcam in a well-lit environment.
- The red dots should latch onto your irises.
- Move your eyes around to see the **Gaze Direction** update.
- Blink naturally to see the **Blink Status** change.

## Important Note

This application does NOT use OpenCV pupil thresholding as requested. It exclusively relies on MediaPipe's machine learning models for high-accuracy iris tracking.
