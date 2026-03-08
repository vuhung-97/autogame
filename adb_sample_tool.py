import time
import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import numpy as np
from ppadb.client import Client as AdbClient
import os
from PIL import Image, ImageTk

class ADBSampleTool:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Screenshot Tool")
        self.root.geometry("600x700")
        self.root.configure(bg="#2f3640")

        self.device = None
        self.current_screen = None

        self.setup_ui()
        self.connect_adb()

    def setup_ui(self):
        # Header
        header = tk.Label(self.root, text="ADB SCREENSHOT TOOL", fg="white", bg="#2f3640", 
                         font=("Segoe UI", 14, "bold"), pady=10)
        header.pack(fill="x")

        # Khung hiển thị ảnh xem trước
        self.canvas = tk.Canvas(self.root, width=540, height=500, bg="#1e272e", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas_text = self.canvas.create_text(270, 250, text="Chưa có dữ liệu", fill="white")

        # Khung điều khiển nút bấm
        control_frame = tk.Frame(self.root, bg="#2f3640")
        control_frame.pack(fill="x", pady=10)

        self.btn_capture = tk.Button(control_frame, text="📸 CHỤP ẢNH", command=self.capture_screen, 
                                     bg="#44bd32", fg="white", font=("Segoe UI", 10, "bold"), 
                                     padx=20, pady=10, bd=0, cursor="hand2")
        self.btn_capture.pack(side="left", padx=50)
        self.btn_compare = tk.Button(control_frame, text="📸 SO SÁNH", command=self.benchmark_capture_speed, 
                                     bg="#44bd32", fg="white", font=("Segoe UI", 10, "bold"), 
                                     padx=20, pady=10, bd=0, cursor="hand2")
        self.btn_compare.pack(side="left", padx=50)
        self.btn_save = tk.Button(control_frame, text="💾 LƯU ẢNH", command=self.save_image, 
                                   bg="#0097e6", fg="white", font=("Segoe UI", 10, "bold"), 
                                   padx=20, pady=10, bd=0, cursor="hand2", state="disabled")
        self.btn_save.pack(side="right", padx=50)

        # Thanh trạng thái
        self.status_var = tk.StringVar(value="Đang chờ kết nối ADB...")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w", 
                              bg="#353b48", fg="white", font=("Segoe UI", 9))
        status_bar.pack(side="bottom", fill="x")

    def connect_adb(self):
        try:
            os.system("adb start-server")
            client = AdbClient(host="127.0.0.1", port=5037)
            devices = client.devices()
            if len(devices) > 0:
                self.device = devices[0]
                self.status_var.set(f"✅ Đã kết nối: {self.device.serial}")
            else:
                self.status_var.set("❌ Không thấy giả lập!")
        except Exception as e:
            self.status_var.set(f"Lỗi ADB: {str(e)}")

    def benchmark_capture_speed(self):
        if not self.device:
            return

        # 1. Đo tốc độ đọc ảnh PNG (Mặc định)
        start_png = time.time()
        for _ in range(10): # Thử nghiệm 10 lần để lấy trung bình
            raw_png = self.device.screencap()
            img_png = cv2.imdecode(np.frombuffer(raw_png, np.uint8), cv2.IMREAD_COLOR)
        end_png = time.time()
        time_png = (end_png - start_png) / 10

        # 2. Đo tốc độ đọc ảnh Raw (Dữ liệu thô)
        start_raw = time.time()
        for _ in range(10):
            with self.device.create_connection() as connection:
                connection.send("shell:screencap")
                raw_binary = connection.read_all()
                
                width = int.from_bytes(raw_binary[0:4], 'little')
                height = int.from_bytes(raw_binary[4:8], 'little')
                img_array = np.frombuffer(raw_binary[12:], dtype=np.uint8)
                
                # Chỉ cần reshape và convert màu (không tốn CPU giải mã thuật toán nén)
                img_raw = img_array[:width*height*4].reshape((height, width, 4))
                img_raw = cv2.cvtColor(img_raw, cv2.COLOR_RGBA2BGR)
        end_raw = time.time()
        time_raw = (end_raw - start_raw) / 10

        speed_up = (time_png / time_raw)
        self.status_var.set(f"""
        ✅ So sánh xong! Raw nhanh hơn PNG ~{speed_up:.2f} lần
        --- KẾT QUẢ TEST (Trung bình 1 lần) ---
        📸 PNG Capture: {time_png:.4f} giây
        🚀 Raw Capture: {time_raw:.4f} giây
        """)

    def capture_screen(self):
        if not self.device:
            self.connect_adb()
            if not self.device: return

        try:
            self.status_var.set("⏳ Đang chụp ảnh...")
            self.root.update()
            raw_data = self.device.screencap()
            self.current_screen = cv2.imdecode(np.frombuffer(raw_data, np.uint8), cv2.IMREAD_COLOR)
            if self.current_screen is not None:
                # Hiển thị lên Canvas
                preview_img = cv2.cvtColor(self.current_screen, cv2.COLOR_BGR2RGB)
                preview_img = Image.fromarray(preview_img)
                preview_img.thumbnail((540, 500))
                self.img_tk = ImageTk.PhotoImage(preview_img)
                self.canvas.delete("all")
                self.canvas.create_image(270, 250, image=self.img_tk, anchor="center")
                self.btn_save.config(state="normal")
        except Exception as e:
            self.status_var.set(f"❌ Lỗi hệ thống: {str(e)}")
            print(f"Chi tiết lỗi: {e}")

    def save_image(self):
        if self.current_screen is None:
            return
        if not os.path.exists("samples"):
            os.makedirs("samples")

        file_path = filedialog.asksaveasfilename(
            initialdir="samples",
            title="Lưu ảnh màn hình",
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"), ("All files", "*.*"))
        )
        if file_path:
            cv2.imwrite(file_path, self.current_screen)
            messagebox.showinfo("Thành công", "Đã lưu ảnh.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ADBSampleTool(root)
    root.mainloop()