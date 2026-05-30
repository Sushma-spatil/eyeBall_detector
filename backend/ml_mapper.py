import numpy as np
from sklearn.ensemble import RandomForestRegressor

class MLMapper:
    def __init__(self):
        self.calib_data = []
        self.model_x = RandomForestRegressor(n_estimators=100, max_depth=10)
        self.model_y = RandomForestRegressor(n_estimators=100, max_depth=10)
        self.is_trained = False
        
        # Grid positions for 16 points (in pixels relative to a standard 1920x1080 screen)
        # Using the same percentages as frontend: 10%, 36%, 63%, 90%
        w, h = 1920, 1080
        xs = [int(w * p) for p in [0.10, 0.36, 0.63, 0.90]]
        ys = [int(h * p) for p in [0.10, 0.36, 0.63, 0.90]]
        self.target_points = [{"x": x, "y": y} for y in ys for x in xs]
        
    def add_sample(self, point_idx, left_ratio, right_ratio, pose):
        # 1-indexed point to 0-indexed array
        idx = point_idx - 1
        if idx < 0 or idx >= 16: return
        
        target = self.target_points[idx]
        
        feature_vector = [
            left_ratio['x'], left_ratio['y'],
            right_ratio['x'], right_ratio['y']
        ]
        
        self.calib_data.append({
            "features": feature_vector,
            "target": [target['x'], target['y']]
        })
        
    def train(self):
        if len(self.calib_data) < 16:
            return False
            
        X = np.array([d["features"] for d in self.calib_data])
        Y = np.array([d["target"] for d in self.calib_data])
        
        self.model_x.fit(X, Y[:, 0])
        self.model_y.fit(X, Y[:, 1])
        
        self.is_trained = True
        return True
        
    def predict(self, left_ratio, right_ratio, pose):
        if not self.is_trained:
            # Fallback to direct mapping (not calibrated)
            combined_x = (left_ratio['x'] + right_ratio['x']) / 2.0
            combined_y = (left_ratio['y'] + right_ratio['y']) / 2.0
            
            # Simple direct mapping ignoring head pose
            # Since the camera is mirrored, 1.0 - x
            mapped_x = (1.0 - combined_x) * 1920
            mapped_y = combined_y * 1080
            return mapped_x, mapped_y, "Raw Eye Mapping"
            
        feature_vector = np.array([[
            left_ratio['x'], left_ratio['y'],
            right_ratio['x'], right_ratio['y']
        ]])
        
        pred_x = self.model_x.predict(feature_vector)[0]
        pred_y = self.model_y.predict(feature_vector)[0]
        
        return pred_x, pred_y, "Random Forest Mapping"
