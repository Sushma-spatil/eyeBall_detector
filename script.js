// DOM Elements
const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const canvasCtx = canvasElement.getContext('2d');

const loadingOverlay = document.getElementById('loading-overlay');

// Status Indicators
const statusCamera = document.getElementById('status-camera');
const statusFace = document.getElementById('status-face');
const statusTracking = document.getElementById('status-tracking');

// Debug Panel Elements
const valGaze = document.getElementById('val-gaze');
const valBlink = document.getElementById('val-blink');
const valAccuracy = document.getElementById('val-accuracy');

// State Variables

// Smoothing for Iris Centers (Exponential Moving Average)
const SMOOTHING_FACTOR = 0.6;
let smoothedLeftIris = null;
let smoothedRightIris = null;

// Landmarks mapping based on requirements
const LEFT_IRIS_INDICES = [468, 469, 470, 471, 472];
const RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477];

// Left Eye Bounding (for EAR and Gaze)
const LEFT_EYE_LEFT = 33;
const LEFT_EYE_RIGHT = 133;
const LEFT_EYE_TOP = 159;
const LEFT_EYE_BOTTOM = 145;

// Right Eye Bounding (for EAR and Gaze)
const RIGHT_EYE_LEFT = 362;
const RIGHT_EYE_RIGHT = 263;
const RIGHT_EYE_TOP = 386;
const RIGHT_EYE_BOTTOM = 374;

// Update Status UI
function updateStatus(element, active) {
    const indicator = element.querySelector('.indicator');
    if (active) {
        element.classList.add('active');
        indicator.classList.remove('red');
        indicator.classList.add('green');
    } else {
        element.classList.remove('active');
        indicator.classList.add('red');
        indicator.classList.remove('green');
    }
}

// Math Utility: Calculate Distance
function getDistance(p1, p2) {
    return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
}

// Calculate Average Point
function getAveragePoint(landmarks, indices, width, height) {
    let sumX = 0, sumY = 0;
    for (let index of indices) {
        sumX += landmarks[index].x * width;
        sumY += landmarks[index].y * height;
    }
    return {
        x: sumX / indices.length,
        y: sumY / indices.length
    };
}

// Calculate Eye Aspect Ratio for Blink Detection
function calculateEAR(landmarks, left_idx, right_idx, top_idx, bottom_idx) {
    const pLeft = landmarks[left_idx];
    const pRight = landmarks[right_idx];
    const pTop = landmarks[top_idx];
    const pBottom = landmarks[bottom_idx];

    const verticalDist = getDistance(pTop, pBottom);
    const horizontalDist = getDistance(pLeft, pRight);

    if (horizontalDist === 0) return 0;
    return verticalDist / horizontalDist;
}

// Determine Gaze Direction
function determineGaze(landmarks, irisCenter, left_idx, right_idx, top_idx, bottom_idx, width, height) {
    const pLeft = { x: landmarks[left_idx].x * width, y: landmarks[left_idx].y * height };
    const pRight = { x: landmarks[right_idx].x * width, y: landmarks[right_idx].y * height };
    const pTop = { x: landmarks[top_idx].x * width, y: landmarks[top_idx].y * height };
    const pBottom = { x: landmarks[bottom_idx].x * width, y: landmarks[bottom_idx].y * height };

    const eyeWidth = pRight.x - pLeft.x;
    const eyeHeight = pBottom.y - pTop.y;
    
    // Relative position of iris center within the eye bounding box (0 to 1)
    const ratioX = (irisCenter.x - pLeft.x) / eyeWidth;
    const ratioY = (irisCenter.y - pTop.y) / eyeHeight;

    let horizontalGaze = "Center";
    let verticalGaze = "";

    // Note: Video is mirrored
    if (ratioX < 0.40) horizontalGaze = "Right";
    else if (ratioX > 0.60) horizontalGaze = "Left";

    if (ratioY < 0.35) verticalGaze = "Up";
    else if (ratioY > 0.65) verticalGaze = "Down";

    if (verticalGaze && horizontalGaze === "Center") {
        return verticalGaze;
    } else if (verticalGaze) {
        return `${verticalGaze} ${horizontalGaze}`;
    }

    return horizontalGaze;
}

// MediaPipe Results Callback
function onResults(results) {
    // Hide loading overlay once results start coming
    if (!loadingOverlay.classList.contains('hidden')) {
        loadingOverlay.classList.add('hidden');
        updateStatus(statusTracking, true);
    }

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        updateStatus(statusFace, true);
        valAccuracy.innerText = "High";
        
        const landmarks = results.multiFaceLandmarks[0];
        const width = canvasElement.width;
        const height = canvasElement.height;

        // 1. Calculate Raw Iris Centers
        const rawLeftIris = getAveragePoint(landmarks, LEFT_IRIS_INDICES, width, height);
        const rawRightIris = getAveragePoint(landmarks, RIGHT_IRIS_INDICES, width, height);

        // 2. Smooth Iris Centers
        if (!smoothedLeftIris) {
            smoothedLeftIris = rawLeftIris;
            smoothedRightIris = rawRightIris;
        } else {
            smoothedLeftIris.x = smoothedLeftIris.x + SMOOTHING_FACTOR * (rawLeftIris.x - smoothedLeftIris.x);
            smoothedLeftIris.y = smoothedLeftIris.y + SMOOTHING_FACTOR * (rawLeftIris.y - smoothedLeftIris.y);
            
            smoothedRightIris.x = smoothedRightIris.x + SMOOTHING_FACTOR * (rawRightIris.x - smoothedRightIris.x);
            smoothedRightIris.y = smoothedRightIris.y + SMOOTHING_FACTOR * (rawRightIris.y - smoothedRightIris.y);
        }

        // 3. Blink Detection
        const leftEAR = calculateEAR(landmarks, LEFT_EYE_LEFT, LEFT_EYE_RIGHT, LEFT_EYE_TOP, LEFT_EYE_BOTTOM);
        const rightEAR = calculateEAR(landmarks, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM);
        const avgEAR = (leftEAR + rightEAR) / 2;
        const blinkThreshold = 0.22; // Tune this threshold as needed

        const leftEyeOpen = leftEAR >= blinkThreshold;
        const rightEyeOpen = rightEAR >= blinkThreshold;

        if (leftEyeOpen && rightEyeOpen) {
            valBlink.innerText = "Open";
            valBlink.style.color = "#FFFFFF";
        } else if (!leftEyeOpen && !rightEyeOpen) {
            valBlink.innerText = "Blink Detected";
            valBlink.style.color = "#FF3B3B";
        } else {
            valBlink.innerText = leftEyeOpen ? "Right Wink" : "Left Wink";
            valBlink.style.color = "#FF3B3B";
        }

        // 4. Draw Iris Dots
        canvasCtx.fillStyle = '#FF3B3B'; // Accent Color
        canvasCtx.shadowColor = '#FF3B3B';
        canvasCtx.shadowBlur = 10;
        
        // Left Eye
        if (leftEyeOpen) {
            canvasCtx.beginPath();
            canvasCtx.arc(smoothedLeftIris.x, smoothedLeftIris.y, 5, 0, 2 * Math.PI);
            canvasCtx.fill();
        }

        // Right Eye
        if (rightEyeOpen) {
            canvasCtx.beginPath();
            canvasCtx.arc(smoothedRightIris.x, smoothedRightIris.y, 5, 0, 2 * Math.PI);
            canvasCtx.fill();
        }
        
        canvasCtx.shadowBlur = 0; // Reset

        // 5. Gaze Direction
        const gaze = determineGaze(landmarks, smoothedLeftIris, LEFT_EYE_LEFT, LEFT_EYE_RIGHT, LEFT_EYE_TOP, LEFT_EYE_BOTTOM, width, height);
        valGaze.innerText = gaze;

    } else {
        updateStatus(statusFace, false);
        valAccuracy.innerText = "Searching...";
        valGaze.innerText = "--";
    }

    canvasCtx.restore();
}

// Initialize MediaPipe FaceMesh
const faceMesh = new FaceMesh({locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
}});

faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true, // Crucial for Iris tracking
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});

faceMesh.onResults(onResults);

// Initialize Camera
let camera = null;

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
        videoElement.srcObject = stream;
        updateStatus(statusCamera, true);

        // Use MediaPipe Camera Utils
        camera = new Camera(videoElement, {
            onFrame: async () => {
                await faceMesh.send({image: videoElement});
            },
            width: 1280,
            height: 720
        });
        camera.start();

    } catch (err) {
        console.error("Error accessing the camera: ", err);
        loadingOverlay.querySelector('p').innerText = "Camera Access Denied. Please allow permissions and refresh.";
        loadingOverlay.querySelector('.spinner').style.display = 'none';
        updateStatus(statusCamera, false);
    }
}

// Start the application
window.onload = () => {
    startCamera();
};
