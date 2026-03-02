import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk
import cv2
import threading
import time
from game_bot_farm_ruong_nguyen_ai import GameAutoBot

MAX_LOG = 200

class MainApp:
    def __init__(self, root):
        self.root = root
        # Truyền thêm callback ảnh cho bot
        self.bot = GameAutoBot(self.log_to_ui, self.show_screen_image)
        self.selected_device_vars = {}
        self.setup_styles()
        self.setup_ui()
        self.refresh_devices_list()

    def setup_styles(self):
        self.root.configure(bg="#f5f6fa")
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def setup_ui(self):
        self.root.title("AUTO FARM RƯƠNG NGUYỀN")
        self.root.geometry("450x600")

        # --- HEADER ---
        header = tk.Frame(self.root, bg="#2f3640", height=50)
        header.pack(fill="x")
        tk.Label(header, text="CONTROL CENTER", fg="white", bg="#2f3640", font=("Segoe UI", 12, "bold")).pack(pady=10)

        main_container = tk.Frame(self.root, bg="#f5f6fa", padx=15, pady=10)
        main_container.pack(fill="both", expand=True)

        # --- DEVICE LIST ---
        list_label_frame = tk.LabelFrame(main_container, text=" 1. Danh sách thiết bị ", font=("Segoe UI", 9, "bold"), bg="white", padx=5, pady=5)
        list_label_frame.pack(fill="x", pady=5)

        self.list_canvas = tk.Canvas(list_label_frame, bg="white", highlightthickness=0, height=100)
        self.scrollbar = ttk.Scrollbar(list_label_frame, orient="vertical", command=self.list_canvas.yview)
        self.list_frame = tk.Frame(self.list_canvas, bg="white")

        self.list_canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        tk.Button(main_container, text="🔄 LÀM MỚI THIẾT BỊ", command=self.refresh_devices_list, bg="#0097e6", fg="white", font=("Segoe UI", 9, "bold"), bd=0, pady=7).pack(fill="x", pady=5)

        # --- CONTROL BUTTONS ---
        btn_container = tk.Frame(main_container, bg="#f5f6fa")
        btn_container.pack(fill="x", pady=10)

        auto_btns_frame = tk.Frame(btn_container, bg="#f5f6fa")
        auto_btns_frame.pack(fill="x", pady=(0, 5))

        self.start_btn = tk.Button(auto_btns_frame, text="▶ ÁM THƯỜNG", command=lambda: self.on_start(False), bg="#44bd32", fg="white", font=("Segoe UI", 10, "bold"), bd=0, height=2)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.nguyen_btn = tk.Button(auto_btns_frame, text="💀 ÁM TỔ TIÊN", command=lambda: self.on_start(True), bg="#8e44ad", fg="white", font=("Segoe UI", 10, "bold"), bd=0, height=2)
        self.nguyen_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))

        self.stop_btn = tk.Button(btn_container, text="⏹ DỪNG TẤT CẢ", command=self.on_stop, bg="#c23616", fg="white", font=("Segoe UI", 10, "bold"), bd=0, height=2)
        self.stop_btn.pack(fill="x")

        # --- LOG AREA ---
        self.log_area = scrolledtext.ScrolledText(
            main_container, font=("Consolas", 9), bg="#1e272e", fg="#ecf0f1", bd=0, height=18  
        )
        self.log_area.pack(fill="x", pady=5)
        self.log_area.config(state="disabled", height=16)  # Đặt chiều cao cố định

        # --- IMAGE VIEW AREA ---
        self.img_frame = tk.Frame(main_container, bg="#222", height=200)
        self.img_frame.pack(fill="both", expand=False, pady=(0, 5))
        self.img_label = tk.Label(self.img_frame, bg="#222")
        self.img_label.pack(fill="both", expand=True)

    def log_to_ui(self, msg, window_name="System"):
        timestamp = time.strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] [{window_name}] ➜ {msg}\n"
        self.root.after(0, self._update_log_text, full_msg)

    def _update_log_text(self, msg):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, msg)
        line_count = int(self.log_area.index('end-1c').split('.')[0])
        if line_count > MAX_LOG:
            self.log_area.delete('1.0', '2.0')
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    # Hàm hiển thị ảnh lên vùng xem ảnh
    def show_screen_image(self, img_np):
        if img_np is None:
            return
        img = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
        max_width, max_height = 400, 350  # Kích thước tối đa vùng xem ảnh
        img.thumbnail((max_width, max_height), Image.LANCZOS)  # Giữ đúng tỷ lệ
        self.photo = ImageTk.PhotoImage(img)
        self.img_label.config(image=self.photo)
        self.img_label.image = self.photo

    def refresh_devices_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.selected_device_vars = {}

        def task():
            devices = self.bot.refresh_devices()
            self.root.after(0, lambda: self._draw_device_checkboxes(devices))

        threading.Thread(target=task, daemon=True).start()

    def _draw_device_checkboxes(self, devices):
        if not devices:
            self.log_to_ui("Không tìm thấy thiết bị nào!")
            return

        for dev in devices:
            var = tk.BooleanVar()
            serial = dev.serial
            cb = tk.Checkbutton(self.list_frame, text=f" Device: {serial}",
                               variable=var, bg="white", font=("Segoe UI", 10), anchor="w")
            cb.pack(fill="x", padx=5, pady=2)
            self.selected_device_vars[serial] = (var, dev)

        self.list_frame.update_idletasks()
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))
        self.log_to_ui(f"Tìm thấy {len(devices)} thiết bị.")

    def on_start(self, is_to_tien):
        active_run = {s: d for s, (v, d) in self.selected_device_vars.items() if v.get()}

        if not active_run:
            self.log_to_ui("LỖI: Bạn chưa chọn thiết bị nào!")
            return

        self.start_btn.config(state="disabled")
        self.nguyen_btn.config(state="disabled")
        self.bot.start(active_run, is_to_tien)
        self.log_to_ui(f"Bắt đầu Auto farm rương nguyền({'map tổ tiên' if is_to_tien else 'map thường'})")

    def on_stop(self):
        self.bot.stop()
        self.start_btn.config(state="normal")
        self.nguyen_btn.config(state="normal")
        self.log_to_ui("--- ĐÃ DỪNG TẤT CẢ ---")
