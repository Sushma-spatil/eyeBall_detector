import numpy as np
from filterpy.kalman import KalmanFilter

class EdgeAmplifier:
    def __init__(self, screen_w=1920, screen_h=1080, margin=0.10):
        self.w = screen_w
        self.h = screen_h
        
        # We know the RF model was trained on targets at 10% and 90%.
        # It physically cannot output values outside this box.
        self.min_x = self.w * margin
        self.max_x = self.w * (1.0 - margin)
        self.min_y = self.h * margin
        self.max_y = self.h * (1.0 - margin)
        
    def amplify(self, x, y):
        # Scale X
        pct_x = (x - self.min_x) / (self.max_x - self.min_x)
        out_x = pct_x * self.w
        
        # Scale Y
        pct_y = (y - self.min_y) / (self.max_y - self.min_y)
        out_y = pct_y * self.h
        
        # Clamp to screen
        out_x = max(0, min(self.w, out_x))
        out_y = max(0, min(self.h, out_y))
        
        return out_x, out_y


class CursorSmoother:
    def __init__(self, ema_alpha=0.20, max_delta=35, deadzone=15):
        self.ema_alpha = ema_alpha
        self.max_delta = max_delta
        self.deadzone = deadzone
        
        self.is_initialized = False
        self.ema_x = 0
        self.ema_y = 0
        
        self.outlier_frames = 0
        self.last_raw_x = 0
        self.last_raw_y = 0
        
    def smooth(self, raw_x, raw_y, confidence=1.0):
        if confidence < 0.6:
            # Low confidence: freeze cursor
            if not self.is_initialized:
                return raw_x, raw_y
            return self.ema_x, self.ema_y
            
        if not self.is_initialized:
            self.ema_x = raw_x
            self.ema_y = raw_y
            self.last_raw_x = raw_x
            self.last_raw_y = raw_y
            self.is_initialized = True
            return raw_x, raw_y
            
        # Outlier Rejection
        raw_jump = np.hypot(raw_x - self.last_raw_x, raw_y - self.last_raw_y)
        if raw_jump > 150:
            self.outlier_frames += 1
            if self.outlier_frames < 3:
                # Reject this frame, return current EMA
                return self.ema_x, self.ema_y
        else:
            self.outlier_frames = 0
            
        self.last_raw_x = raw_x
        self.last_raw_y = raw_y
            
        # Gaze Locking (Deadzone)
        dist_to_ema = np.hypot(raw_x - self.ema_x, raw_y - self.ema_y)
        if dist_to_ema < self.deadzone:
            # Locked! Do not update EMA.
            return self.ema_x, self.ema_y
            
        target_x = raw_x
        target_y = raw_y
        
        # Max Delta Clamping (Velocity limiting)
        move_dist = np.hypot(target_x - self.ema_x, target_y - self.ema_y)
        if move_dist > self.max_delta:
            ratio = self.max_delta / move_dist
            target_x = self.ema_x + (target_x - self.ema_x) * ratio
            target_y = self.ema_y + (target_y - self.ema_y) * ratio
            
        # Apply EMA
        self.ema_x = (self.ema_alpha * target_x) + ((1 - self.ema_alpha) * self.ema_x)
        self.ema_y = (self.ema_alpha * target_y) + ((1 - self.ema_alpha) * self.ema_y)
        
        return self.ema_x, self.ema_y
