import time
import math

class BlinkDetector:
    def __init__(self):
        self.EAR_THRESHOLD = 0.20  # Below this, eye is closed
        self.DOUBLE_BLINK_WINDOW = 0.4  # max seconds between two blinks
        self.LONG_BLINK_THRESHOLD = 1.0  # seconds eye must be closed for long blink
        self.DEBOUNCE_TIME = 0.5  # seconds to ignore blinks after an action
        
        self.eye_closed = False
        self.closed_start_time = 0
        self.last_blink_time = 0
        self.last_action_time = 0
        
        self.pending_single_blink = False
        self.drag_mode = False

    def get_distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def calculate_ear(self, eye_points):
        # eye_points: [p33, p160, p158, p133, p153, p144]
        # vertical 1: p160 - p144 (idx 1 and 5)
        # vertical 2: p158 - p153 (idx 2 and 4)
        # horizontal: p33 - p133 (idx 0 and 3)
        if not eye_points or len(eye_points) < 6:
            return 1.0
            
        v1 = self.get_distance(eye_points[1], eye_points[5])
        v2 = self.get_distance(eye_points[2], eye_points[4])
        h = self.get_distance(eye_points[0], eye_points[3])
        
        if h == 0:
            return 1.0
            
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def detect_gestures(self, left_ear, right_ear):
        avg_ear = (left_ear + right_ear) / 2.0
        now = time.time()
        
        gesture = None
        
        # Debounce check
        if now - self.last_action_time < self.DEBOUNCE_TIME:
            self.pending_single_blink = False
            return gesture

        # Process pending single blink if window expired
        if self.pending_single_blink and (now - self.last_blink_time > self.DOUBLE_BLINK_WINDOW):
            gesture = "SINGLE_BLINK"
            self.pending_single_blink = False
            self.last_action_time = now
            return gesture

        if avg_ear < self.EAR_THRESHOLD:
            if not self.eye_closed:
                self.eye_closed = True
                self.closed_start_time = now
            else:
                # Check for long blink (drag toggle) while eye is still closed
                duration = now - self.closed_start_time
                if duration >= self.LONG_BLINK_THRESHOLD:
                    self.drag_mode = not self.drag_mode
                    gesture = "DRAG_TOGGLE"
                    self.last_action_time = now
                    # Reset so it doesn't repeatedly toggle
                    self.eye_closed = False
                    self.pending_single_blink = False
        else:
            if self.eye_closed:
                self.eye_closed = False
                duration = now - self.closed_start_time
                
                # If it was a short blink
                if duration < self.LONG_BLINK_THRESHOLD and (now - self.last_action_time >= self.DEBOUNCE_TIME):
                    # Check if this completes a double blink
                    if self.pending_single_blink and (now - self.last_blink_time <= self.DOUBLE_BLINK_WINDOW):
                        gesture = "DOUBLE_BLINK"
                        self.pending_single_blink = False
                        self.last_action_time = now
                    else:
                        # Queue a single blink
                        self.pending_single_blink = True
                        self.last_blink_time = now
                        
        return gesture
