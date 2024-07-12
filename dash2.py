import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import airsim
import numpy as np
import cv2
import math
import threading
import time
import google.generativeai as genai
import pyautogui
from datetime import datetime
import pyttsx3

# Import the global variable and Gemini API function


class ModernUI(ttk.Style):
    def __init__(self):
        super().__init__()
        self.theme_create("modern", parent="alt", settings={
            "TFrame": {"configure": {"background": "#2E3440"}},
            "TLabel": {"configure": {"background": "#2E3440", "foreground": "#ECEFF4"}},
            "TButton": {"configure": {"background": "#5E81AC", "foreground": "#ECEFF4"}},
            "TEntry": {"configure": {"fieldbackground": "#3B4252", "foreground": "#ECEFF4"}},
            "Canvas": {"configure": {"background": "#3B4252"}},
        })
        self.theme_use("modern")

class AirSimDashboard:
    def __init__(self, master):
        self.master = master
        self.master.title("AirSim Dashboard")
        self.master.geometry("1280x720")
        self.master.configure(bg="#2E3440")

        ModernUI()
        self.setup_ui()
        self.setup_airsim()

        self.path_points = []
        self.map_center = [0, 0]
        self.map_scale = 1

        self.update_airsim_view()
        self.update_map()
        self.update_gemini_text()

        # Screen recording setup
        self.is_recording = False
        self.start_screen_recording()

        # Bind the closing event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        title_label = ttk.Label(main_frame, text="AirSim Dashboard", font=("Segoe UI", 28, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.airsim_view = ttk.Label(main_frame)
        self.airsim_view.grid(row=1, column=0, padx=(0, 20), sticky=(tk.W, tk.E, tk.N, tk.S))

        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        right_panel.rowconfigure(2, weight=1)
        right_panel.columnconfigure(0, weight=1)

        self.map_canvas = tk.Canvas(right_panel, width=300, height=300, bg="#3B4252", highlightthickness=0)
        self.map_canvas.grid(row=0, column=0, pady=(0, 20), sticky=(tk.W, tk.E))

        self.position_label = ttk.Label(right_panel, text="Position: X: 0.00, Y: 0.00", font=("Segoe UI", 12))
        self.position_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        self.dynamic_text = tk.Text(right_panel, height=10, wrap=tk.WORD, font=("Segoe UI", 12), bg="#3B4252", fg="#ECEFF4", insertbackground="#ECEFF4")
        self.dynamic_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dynamic_text.insert(tk.END, "Initializing Gemini API responses...")

        text_scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.dynamic_text.yview)
        text_scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.dynamic_text.configure(yscrollcommand=text_scrollbar.set)

    def setup_airsim(self):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()

        camera_pose = airsim.Pose(airsim.Vector3r(0, 0, -20), airsim.to_quaternion(math.radians(-90), 0, 0))
        self.client.simSetCameraPose("0", camera_pose)

    def update_airsim_view(self):
        responses = self.client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
        response = responses[0]
        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        img_rgb = img1d.reshape(response.height, response.width, 3)
        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
        img_rgb = cv2.resize(img_rgb, (800, 600))
        img_tk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
        self.airsim_view.configure(image=img_tk)
        self.airsim_view.image = img_tk
        self.master.after(100, self.update_airsim_view)

    def update_map(self):
        drone_pose = self.client.simGetVehiclePose()
        x, y = drone_pose.position.x_val, drone_pose.position.y_val

        self.path_points.append((x, y))
        self.path_points = self.path_points[-1000:]
        self.map_center = [x, y]

        self.map_canvas.delete("all")

        for i in range(1, len(self.path_points)):
            x1, y1 = self.path_points[i-1]
            x2, y2 = self.path_points[i]
            self.map_canvas.create_line(
                150 + (x1 - self.map_center[0]) * self.map_scale,
                150 - (y1 - self.map_center[1]) * self.map_scale,
                150 + (x2 - self.map_center[0]) * self.map_scale,
                150 - (y2 - self.map_center[1]) * self.map_scale,
                fill="#A3BE8C", width=2
            )

        self.map_canvas.create_oval(147, 147, 153, 153, fill="#BF616A", outline="#BF616A")

        self.position_label.config(text=f"Position: X: {x:.2f}, Y: {y:.2f}")

        self.master.after(100, self.update_map)

    def update_gemini_text(self):
        def gemini_thread():
            while True:
                try:
                    current_value = "break = applied"
                    system_prompt = "You are a AI driving assistant. You emergency braked to avoid an animal. You are being provided car telemetry data. Explain why you autonomously performed this action by using this information. Do this to gain trust of the user sitting in the car. Keep it very concise."
                    prompt = system_prompt + current_value
                    genai.configure(api_key="AIzaSyAgLowqXpgZhLExcw_f-6o051hqvT9G92Q")
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    api_response = response._result.candidates[0].content.parts[0].text
                    time.sleep(10)
                    self.master.after(0, self.update_text_box, api_response)
                    engine = pyttsx3.init()
                    time.sleep(1.5)
                    engine.say(api_response)
                    engine.runAndWait()
                    time.sleep(15)
                except Exception as e:
                    print(f"Error in Gemini API call: {e}")
                    time.sleep(5)

        threading.Thread(target=gemini_thread, daemon=True).start()

    def update_text_box(self, new_text):
        self.dynamic_text.config(state=tk.NORMAL)
        self.dynamic_text.delete(1.0, tk.END)
        self.dynamic_text.insert(tk.END, new_text)
        self.dynamic_text.config(state=tk.DISABLED)
        self.dynamic_text.see(tk.END)

    def start_screen_recording(self):
        self.is_recording = True
        threading.Thread(target=self.screen_record, daemon=True).start()

    def screen_record(self):
        SCREEN_SIZE = tuple(pyautogui.size())
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 10.0
        out = cv2.VideoWriter(f"dashboard_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4", fourcc, fps, SCREEN_SIZE)

        while self.is_recording:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
            time.sleep(1/fps)

        out.release()

    def on_closing(self):
        self.is_recording = False
        time.sleep(1)  # Give time for the recording thread to finish
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AirSimDashboard(root)
    root.mainloop()