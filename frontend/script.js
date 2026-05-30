// DOM Elements
const statusTracking = document.getElementById('status-tracking');
const statusCalibration = document.getElementById('status-calibration');

const valHovered = document.getElementById('val-hovered');
const valWgX = document.getElementById('val-wg-x');
const valWgY = document.getElementById('val-wg-y');
const valCoords = document.getElementById('val-coords');
const valEar = document.getElementById('val-ear');

const calibrationOverlay = document.getElementById('calibration-overlay');
const calibrationDotsContainer = document.getElementById('calibration-dots-container');
const btnStartCalibration = document.getElementById('btn-start-calibration');
const btnRecalibrate = document.getElementById('btn-recalibrate');
const diagPoints = document.getElementById('diag-points');

const customCursor = document.getElementById('custom-cursor');

// State
let isCalibrating = false;
let currentlyHoveredElement = null;
let pointsCompleted = 0;
const CLICKS_PER_POINT = 5;

// Fluid Smoothing (Optimized for WebGazer's noise profile)
class CursorSmoother {
    constructor(emaAlpha=0.15) {
        this.emaAlpha = emaAlpha;
        this.initialized = false;
        this.emaX = window.innerWidth / 2;
        this.emaY = window.innerHeight / 2;
    }

    smooth(rawX, rawY) {
        if (!this.initialized) {
            this.emaX = rawX;
            this.emaY = rawY;
            this.initialized = true;
            return {x: rawX, y: rawY};
        }

        // Apply simple EMA to cut through WebGazer noise without blocking movement
        this.emaX = (this.emaAlpha * rawX) + ((1 - this.emaAlpha) * this.emaX);
        this.emaY = (this.emaAlpha * rawY) + ((1 - this.emaAlpha) * this.emaY);

        return {x: this.emaX, y: this.emaY};
    }
}

const smoother = new CursorSmoother(0.15);

// Calibration Points (9-point grid)
const calibPoints = [
    {x: '10%', y: '10%'}, {x: '50%', y: '10%'}, {x: '90%', y: '10%'},
    {x: '10%', y: '50%'}, {x: '50%', y: '50%'}, {x: '90%', y: '50%'},
    {x: '10%', y: '90%'}, {x: '50%', y: '90%'}, {x: '90%', y: '90%'}
];

function initWebGazer() {
    webgazer.setGazeListener((data, clock) => {
        if (data == null) {
            return;
        }

        const rawX = data.x;
        const rawY = data.y;

        // Apply Military-Grade Smoothing
        const smoothed = smoother.smooth(rawX, rawY);

        // Update Diagnostics
        valWgX.innerText = Math.round(rawX);
        valWgY.innerText = Math.round(rawY);
        valCoords.innerText = `${Math.round(smoothed.x)}, ${Math.round(smoothed.y)}`;

        // Move Virtual Cursor
        if (!isCalibrating) {
            customCursor.style.left = `${smoothed.x}px`;
            customCursor.style.top = `${smoothed.y}px`;
            simulateHover(smoothed.x, smoothed.y);
        }

    }).begin();

    // Hide the default WebGazer video overlay if you want it invisible
    // webgazer.showVideoPreview(false).showPredictionPoints(false);
    
    // We keep video preview visible so you can see your face tracking
    webgazer.showPredictionPoints(false);

    updateStatus(statusTracking, true);
}

// UI Helpers
function updateStatus(element, active) {
    if (!element) return;
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

function simulateHover(x, y) {
    customCursor.style.display = 'none'; // Temporarily hide to get element underneath
    let hoveredElement = document.elementFromPoint(x, y);
    customCursor.style.display = 'block';

    let interactiveElement = hoveredElement ? hoveredElement.closest('.grid-button, .btn-close, .btn-primary') : null;

    if (interactiveElement !== currentlyHoveredElement) {
        if (currentlyHoveredElement) {
            currentlyHoveredElement.classList.remove('hovered');
        }
        currentlyHoveredElement = interactiveElement;
        
        if (currentlyHoveredElement) {
            currentlyHoveredElement.classList.add('hovered');
            valHovered.innerText = currentlyHoveredElement.innerText.split('\n')[0] || currentlyHoveredElement.tagName;
        } else {
            valHovered.innerText = "None";
        }
    }
}

// Calibration Logic
function startCalibration() {
    isCalibrating = true;
    pointsCompleted = 0;
    diagPoints.innerText = "0";
    
    calibrationOverlay.classList.remove('hidden');
    calibrationDotsContainer.classList.remove('hidden');
    btnStartCalibration.style.display = 'none';
    
    // Clear previous calibration memory in WebGazer
    webgazer.clearData();
    
    calibrationDotsContainer.innerHTML = '';
    
    // Create 9 dots
    calibPoints.forEach((pos, idx) => {
        let dot = document.createElement('div');
        dot.className = 'calibration-dot';
        dot.style.left = pos.x;
        dot.style.top = pos.y;
        dot.dataset.clicks = 0;
        
        dot.addEventListener('click', function(e) {
            let clicks = parseInt(this.dataset.clicks);
            clicks++;
            this.dataset.clicks = clicks;
            
            // Explicitly force WebGazer to record this click for calibration
            if (window.webgazer) {
                window.webgazer.recordScreenPosition(e.clientX, e.clientY, 'click');
            }
            
            // Visual feedback
            this.style.transform = `translate(-50%, -50%) scale(${1 + (clicks * 0.2)})`;
            
            if (clicks >= CLICKS_PER_POINT) {
                this.style.backgroundColor = 'var(--success-color)';
                this.style.pointerEvents = 'none';
                pointsCompleted++;
                diagPoints.innerText = pointsCompleted;
                
                if (pointsCompleted >= 9) {
                    endCalibration();
                }
            }
        });
        
        calibrationDotsContainer.appendChild(dot);
    });
}

function endCalibration() {
    isCalibrating = false;
    calibrationOverlay.classList.add('hidden');
    calibrationDotsContainer.classList.add('hidden');
    updateStatus(statusCalibration, true);
}

// Blink Detection Engine
function getEAR(landmarks, indices) {
    const outer = landmarks[indices[0]];
    const inner = landmarks[indices[1]];
    const top = landmarks[indices[2]];
    const bottom = landmarks[indices[3]];

    const width = Math.hypot(outer.x - inner.x, outer.y - inner.y);
    const height = Math.hypot(top.x - bottom.x, top.y - bottom.y);
    return width > 0 ? height / width : 0;
}

function startBlinkDetector() {
    const video = document.getElementById('webgazerVideoFeed');
    if (!video) {
        setTimeout(startBlinkDetector, 1000); // WebGazer hasn't injected video yet
        return;
    }
    console.log("WebGazer Video found. Initializing Blink Detector...");

    const faceMesh = new FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${file}`
    });
    
    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults((results) => {
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            const landmarks = results.multiFaceLandmarks[0];
            
            // Left eye: 33 (outer), 133 (inner), 159 (top), 145 (bottom)
            const leftEAR = getEAR(landmarks, [33, 133, 159, 145]);
            // Right eye: 362 (inner), 263 (outer), 386 (top), 374 (bottom)
            const rightEAR = getEAR(landmarks, [362, 263, 386, 374]);
            
            const ear = (leftEAR + rightEAR) / 2.0;
            if(valEar) valEar.innerText = ear.toFixed(2);
            
            // Trigger Click on Blink (threshold < 0.22)
            if (ear < 0.22) {
                let now = Date.now();
                if (!window.lastBlink || now - window.lastBlink > 1000) {
                    console.log("Blink Click Triggered! EAR:", ear.toFixed(2));
                    simulateClick();
                    window.lastBlink = now;
                }
            }
        }
    });

    async function processVideo() {
        if (video.readyState >= 2 && !isCalibrating) {
            await faceMesh.send({image: video});
        }
        requestAnimationFrame(processVideo);
    }
    processVideo();
}

// Simulate Click Mechanics
function simulateClick() {
    if (currentlyHoveredElement) {
        customCursor.classList.add('clicking');
        setTimeout(() => customCursor.classList.remove('clicking'), 200);
        
        currentlyHoveredElement.classList.add('clicked');
        setTimeout(() => currentlyHoveredElement.classList.remove('clicked'), 300);
        
        currentlyHoveredElement.click();
    }
}

btnStartCalibration.addEventListener('click', startCalibration);
btnRecalibrate.addEventListener('click', startCalibration);

// Start
window.onload = () => {
    initWebGazer();
    startBlinkDetector();
    updateStatus(statusCalibration, false);
};
