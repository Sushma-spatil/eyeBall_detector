import tkinter as tk
import time

class CalibrationUI:
    def __init__(self, on_complete):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(background='black')
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        
        self.points = [
            ("CENTER", self.screen_w // 2, self.screen_h // 2),
            ("LEFT", 50, self.screen_h // 2),
            ("RIGHT", self.screen_w - 50, self.screen_h // 2),
            ("TOP", self.screen_w // 2, 50),
            ("BOTTOM", self.screen_w // 2, self.screen_h - 50)
        ]
        
        self.current_point_idx = 0
        self.samples = []
        self.calibrated_data = {}
        
        self.on_complete = on_complete
        self.is_active = True
        
        self.state = "INIT"
        self.state_start_time = time.time()
        
        self.instruction_text = self.canvas.create_text(
            self.screen_w // 2, self.screen_h // 2 - 70,
            text="",
            fill="white", font=("Arial", 36, "bold")
        )
        
        self.progress_text = self.canvas.create_text(
            self.screen_w // 2, self.screen_h // 2 + 70,
            text="",
            fill="lightgray", font=("Arial", 20)
        )
        
        self.dot = self.canvas.create_oval(0, 0, 0, 0, fill="red")
        
        self.root.update()
        self.setup_point()

    def setup_point(self):
        if self.current_point_idx >= len(self.points):
            self.finish()
            return
            
        name, x, y = self.points[self.current_point_idx]
        print(f"Calibration active point: {name}")
        
        self.canvas.itemconfig(self.instruction_text, text=f"Look at the {name} dot")
        self.canvas.itemconfig(self.progress_text, text=f"Step {self.current_point_idx + 1}/{len(self.points)}")
        
        r = 30 # Large dot
        self.canvas.coords(self.dot, x-r, y-r, x+r, y+r)
        self.canvas.itemconfig(self.dot, fill="red")
        
        self.samples = []
        self.state = "WAIT"
        self.state_start_time = time.time()

    def add_sample(self, ratio_x, ratio_y):
        if self.state == "COLLECT":
            self.samples.append((ratio_x, ratio_y))

    def update(self):
        if not self.is_active:
            return
            
        try:
            self.root.update()
        except tk.TclError:
            self.is_active = False
            return
            
        now = time.time()
        elapsed = now - self.state_start_time
        
        if self.state == "WAIT":
            if elapsed > 1.5:
                self.state = "COLLECT"
                self.state_start_time = now
                self.canvas.itemconfig(self.dot, fill="yellow") # Visual feedback
        elif self.state == "COLLECT":
            if elapsed > 1.5:
                self.process_point()

    def process_point(self):
        name = self.points[self.current_point_idx][0]
        if self.samples:
            avg_x = sum([s[0] for s in self.samples]) / len(self.samples)
            avg_y = sum([s[1] for s in self.samples]) / len(self.samples)
            self.calibrated_data[name] = (avg_x, avg_y)
        else:
            self.calibrated_data[name] = (0.5, 0.5)
            
        self.current_point_idx += 1
        self.setup_point()

    def finish(self):
        self.is_active = False
        try:
            self.root.destroy()
        except:
            pass
        self.on_complete(self.calibrated_data)


class CalibrationManager:
    def __init__(self):
        self.is_calibrated = False
        self.bounds = {
            'min_x': 0.4, 'max_x': 0.6,
            'min_y': 0.4, 'max_y': 0.6
        }

    def process_results(self, data):
        if not data:
            print("Calibration failed or skipped. Using defaults.")
            self.is_calibrated = True
            return

        if "LEFT" in data and "RIGHT" in data:
            self.bounds['min_x'] = min(data["RIGHT"][0], data["LEFT"][0])
            self.bounds['max_x'] = max(data["RIGHT"][0], data["LEFT"][0])
                
        if "TOP" in data and "BOTTOM" in data:
            self.bounds['min_y'] = min(data["TOP"][1], data["BOTTOM"][1])
            self.bounds['max_y'] = max(data["TOP"][1], data["BOTTOM"][1])
            
        # Add buffer
        if self.bounds['max_x'] - self.bounds['min_x'] < 0.01:
            self.bounds['max_x'] += 0.01
        if self.bounds['max_y'] - self.bounds['min_y'] < 0.01:
            self.bounds['max_y'] += 0.01
            
        self.is_calibrated = True
        print(f"Calibration complete: {self.bounds}")

    def normalize(self, raw_x, raw_y):
        norm_x = (raw_x - self.bounds['min_x']) / (self.bounds['max_x'] - self.bounds['min_x'])
        norm_y = (raw_y - self.bounds['min_y']) / (self.bounds['max_y'] - self.bounds['min_y'])
        norm_x = 1.0 - norm_x # Mirror inversion
        return norm_x, norm_y
