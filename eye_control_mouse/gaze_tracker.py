import cv2
import mediapipe as mp

class GazeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye boundaries for EAR and gaze ratio
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        
        # Iris indices
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        return results

    def get_landmarks(self, landmarks, indices, img_w, img_h):
        points = []
        for idx in indices:
            lm = landmarks.landmark[idx]
            points.append((int(lm.x * img_w), int(lm.y * img_h)))
        return points

    def calculate_iris_center(self, iris_landmarks):
        if not iris_landmarks:
            return None
        x = sum([p[0] for p in iris_landmarks]) / len(iris_landmarks)
        y = sum([p[1] for p in iris_landmarks]) / len(iris_landmarks)
        return (x, y)

    def get_gaze_ratio(self, eye_points, iris_center):
        if not eye_points or not iris_center:
            return 0.5, 0.5
            
        min_x = min([p[0] for p in eye_points])
        max_x = max([p[0] for p in eye_points])
        min_y = min([p[1] for p in eye_points])
        max_y = max([p[1] for p in eye_points])
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width == 0 or height == 0:
            return 0.5, 0.5
            
        ratio_x = (iris_center[0] - min_x) / width
        ratio_y = (iris_center[1] - min_y) / height
        
        return ratio_x, ratio_y
