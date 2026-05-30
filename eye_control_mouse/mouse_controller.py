import pyautogui

# Fail-safe to avoid crashing if mouse hits corner
pyautogui.FAILSAFE = False

class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        
        self.cursor_x = self.screen_w / 2
        self.cursor_y = self.screen_h / 2
        
        self.SMOOTHING = 0.15  # Alpha for EMA (lower = smoother but more lag)

    def update_position(self, target_ratio_x, target_ratio_y):
        # Map ratio (0-1) to screen coordinates
        target_x = target_ratio_x * self.screen_w
        target_y = target_ratio_y * self.screen_h
        
        # Clamp to screen
        target_x = max(0, min(self.screen_w, target_x))
        target_y = max(0, min(self.screen_h, target_y))
        
        # EMA Smoothing
        self.cursor_x = self.cursor_x + (target_x - self.cursor_x) * self.SMOOTHING
        self.cursor_y = self.cursor_y + (target_y - self.cursor_y) * self.SMOOTHING
        
        # Move actual mouse
        try:
            pyautogui.moveTo(self.cursor_x, self.cursor_y, _pause=False)
        except Exception as e:
            print(f"Mouse move error: {e}")

    def left_click(self):
        try:
            pyautogui.click()
            print("Action: Left Click")
        except Exception as e:
            print(f"Click error: {e}")

    def right_click(self):
        try:
            pyautogui.click(button='right')
            print("Action: Right Click")
        except Exception as e:
            print(f"Right click error: {e}")

    def set_drag(self, dragging):
        try:
            if dragging:
                pyautogui.mouseDown()
                print("Action: Drag Start (Mouse Down)")
            else:
                pyautogui.mouseUp()
                print("Action: Drag End (Mouse Up)")
        except Exception as e:
            print(f"Drag error: {e}")
