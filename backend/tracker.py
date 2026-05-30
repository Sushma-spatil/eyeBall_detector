import cv2
import mediapipe as mp
import numpy as np

class EyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        self.LEFT_EYE_CORNERS = [33, 133] # Left corner, Right corner of Left eye
        self.RIGHT_EYE_CORNERS = [362, 263] # Left corner, Right corner of Right eye
        self.LEFT_EYE_LIDS = [159, 145] # Top, Bottom
        self.RIGHT_EYE_LIDS = [386, 374] # Top, Bottom
        
        # 3D points for Head Pose (approximate generic face model)
        self.face_3d = np.array([
            (0.0, 0.0, 0.0),            # Nose tip
            (0.0, -330.0, -65.0),       # Chin
            (-225.0, 170.0, -135.0),    # Left eye left corner
            (225.0, 170.0, -135.0),     # Right eye right corner
            (-150.0, -150.0, -125.0),   # Left Mouth corner
            (150.0, -150.0, -125.0)     # Right Mouth corner
        ], dtype=np.float64)

    def _get_normalized_eye_3d(self, landmarks, iris_idx, corners_idx, lids_idx):
        def get_pt(idx):
            p = landmarks[idx]
            return np.array([p.x, p.y, p.z])
            
        iris_pts = np.array([get_pt(i) for i in iris_idx])
        iris_center = np.mean(iris_pts, axis=0)
        
        left_c = get_pt(corners_idx[0])
        right_c = get_pt(corners_idx[1])
        top_c = get_pt(lids_idx[0])
        bottom_c = get_pt(lids_idx[1])
        
        vec_w = right_c - left_c
        w_sq = np.dot(vec_w, vec_w)
        
        if w_sq == 0:
            return 0.5, 0.5, 0.0
            
        vec_iris_w = iris_center - left_c
        nx = np.dot(vec_iris_w, vec_w) / w_sq
        
        # Use rigid face axis (forehead to chin) for vertical projection
        forehead = get_pt(10)
        chin = get_pt(152)
        head_vert = chin - forehead
        h_sq = np.dot(head_vert, head_vert)
        
        vec_iris_h = iris_center - forehead
        ny = np.dot(vec_iris_h, head_vert) / h_sq
        
        w_dist = np.sqrt(w_sq)
        lid_dist = np.linalg.norm(bottom_c - top_c)
        ear = lid_dist / w_dist if w_dist > 0 else 0
        
        return float(nx), float(ny), float(ear)

    def _get_head_pose(self, mesh_points, img_w, img_h):
        face_2d = np.array([
            mesh_points[1],     # Nose tip
            mesh_points[152],   # Chin
            mesh_points[33],    # Left eye left corner
            mesh_points[263],   # Right eye right corner
            mesh_points[61],    # Left mouth corner
            mesh_points[291]    # Right mouth corner
        ], dtype=np.float64)
        
        focal_length = 1 * img_w
        cam_matrix = np.array([
            [focal_length, 0, img_h / 2],
            [0, focal_length, img_w / 2],
            [0, 0, 1]
        ])
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)
        
        success, rot_vec, trans_vec = cv2.solvePnP(self.face_3d, face_2d, cam_matrix, dist_coeffs)
        
        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        
        pitch = angles[0] * 360
        yaw = angles[1] * 360
        roll = angles[2] * 360
        
        return pitch, yaw, roll

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        img_h, img_w, _ = frame.shape
        data = {"face_detected": False}
        
        if results.multi_face_landmarks:
            data["face_detected"] = True
            
            landmarks = results.multi_face_landmarks[0].landmark
            
            # True 3D Normalization and EAR
            lx, ly, l_ear = self._get_normalized_eye_3d(landmarks, self.LEFT_IRIS, self.LEFT_EYE_CORNERS, self.LEFT_EYE_LIDS)
            rx, ry, r_ear = self._get_normalized_eye_3d(landmarks, self.RIGHT_IRIS, self.RIGHT_EYE_CORNERS, self.RIGHT_EYE_LIDS)
            
            # Head Pose (kept for logging/diagnostics, but not used in primary eye mapping)
            mesh_points = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in landmarks])
            pitch, yaw, roll = self._get_head_pose(mesh_points, img_w, img_h)
            
            data["left_ratio"] = {"x": lx, "y": ly}
            data["right_ratio"] = {"x": rx, "y": ry}
            data["combined_ratio"] = {"x": (lx + rx) / 2.0, "y": (ly + ry) / 2.0}
            data["ear"] = (l_ear + r_ear) / 2.0
            data["pose"] = {"pitch": pitch, "yaw": yaw, "roll": roll}
            
        return data
