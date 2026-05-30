import cv2
import numpy as np
import time
from gaze_tracker import GazeTracker
from calibration import CalibrationManager, CalibrationUI
from blink_detector import BlinkDetector
from mouse_controller import MouseController

def main():
    # Initialize components
    gaze_tracker = GazeTracker()
    blink_detector = BlinkDetector()
    mouse_controller = MouseController()
    calib_manager = CalibrationManager()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Starting calibration...")
    
    def on_calib_complete(data):
        calib_manager.process_results(data)
        
    calib_ui = CalibrationUI(on_calib_complete)
    
    print("Look at the red dot for calibration...")
    
    # Main Loop
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue
            
        frame = cv2.flip(frame, 1) # Mirror image for intuitive debugging
        
        # Process Gaze
        results = gaze_tracker.process_frame(frame)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            img_h, img_w, _ = frame.shape
            
            # Extract eye landmarks
            left_eye_points = gaze_tracker.get_landmarks(landmarks, gaze_tracker.LEFT_EYE, img_w, img_h)
            right_eye_points = gaze_tracker.get_landmarks(landmarks, gaze_tracker.RIGHT_EYE, img_w, img_h)
            
            left_iris_points = gaze_tracker.get_landmarks(landmarks, gaze_tracker.LEFT_IRIS, img_w, img_h)
            right_iris_points = gaze_tracker.get_landmarks(landmarks, gaze_tracker.RIGHT_IRIS, img_w, img_h)
            
            # Calculate Iris centers
            left_iris_center = gaze_tracker.calculate_iris_center(left_iris_points)
            right_iris_center = gaze_tracker.calculate_iris_center(right_iris_points)
            
            # Calculate Eye Aspect Ratio (EAR)
            left_ear = blink_detector.calculate_ear(left_eye_points)
            right_ear = blink_detector.calculate_ear(right_eye_points)
            
            # Calculate raw gaze ratios
            left_ratio_x, left_ratio_y = gaze_tracker.get_gaze_ratio(left_eye_points, left_iris_center)
            
            # Calibration Phase
            if calib_ui.is_active:
                calib_ui.add_sample(left_ratio_x, left_ratio_y)
                calib_ui.update()
            
            # Tracking Phase
            else:
                if calib_manager.is_calibrated:
                    # Normalize and map to screen
                    norm_x, norm_y = calib_manager.normalize(left_ratio_x, left_ratio_y)
                    mouse_controller.update_position(norm_x, norm_y)
                    
                    # Detect Blinks
                    gesture = blink_detector.detect_gestures(left_ear, right_ear)
                    if gesture == "SINGLE_BLINK":
                        mouse_controller.left_click()
                    elif gesture == "DOUBLE_BLINK":
                        mouse_controller.right_click()
                    elif gesture == "DRAG_TOGGLE":
                        mouse_controller.set_drag(blink_detector.drag_mode)
                        
            # Visualization for Debug Window
            if left_eye_points and right_eye_points:
                cv2.polylines(frame, [np.array(left_eye_points, dtype=np.int32)], True, (0, 255, 0), 1)
                cv2.polylines(frame, [np.array(right_eye_points, dtype=np.int32)], True, (0, 255, 0), 1)
            if left_iris_center:
                cv2.circle(frame, (int(left_iris_center[0]), int(left_iris_center[1])), 2, (0, 0, 255), -1)
            if right_iris_center:
                cv2.circle(frame, (int(right_iris_center[0]), int(right_iris_center[1])), 2, (0, 0, 255), -1)
                
            avg_ear = (left_ear + right_ear) / 2.0
            status_text = f"Calibrated: {calib_manager.is_calibrated} | EAR: {avg_ear:.2f}"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            if not calib_ui.is_active and blink_detector.eye_closed:
                cv2.putText(frame, "BLINK DETECTED", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
        cv2.imshow("Eye Control Mouse Debug", frame)
        
        # Press ESC to exit
        if cv2.waitKey(5) & 0xFF == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
