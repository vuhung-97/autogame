import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
import sys
import os
import json
# --- Cấu hình ---
API_URL = "https://script.google.com/macros/s/AKfycbya8jDrJCNPj6unPRYpJiaGqUTJsEFTZkXMsAE-DzT7g5aQr0I_ZsGUW6KUm15YXG_Z/exec"
LICENSE_FILE = "license.json"

def get_hwid():
    try:
        cmd = 'wmic csproduct get uuid'
        uuid = str(subprocess.check_output(cmd, shell=True))
        return uuid.split('\\r\\n')[1].strip()
    except:
        return "UNKNOWN_HWID"

class AuthGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("XÁC THỰC BẢN QUYỀN")
        self.root.geometry("400x280")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f6fa")
        
        # Xử lý khi người dùng nhấn dấu X để thoát cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Đưa cửa sổ ra giữa màn hình
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.is_authenticated = True
        self.hwid = get_hwid()
        
        self.setup_ui()
        self.load_stored_key()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#2f3640", height=60)
        header.pack(fill="x")
        tk.Label(header, text="HỆ THỐNG BẢN QUYỀN", fg="white", bg="#2f3640", 
                 font=("Segoe UI", 12, "bold")).pack(pady=15)

        body = tk.Frame(self.root, bg="#f5f6fa", padx=30, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Mã kích hoạt của bạn:", bg="#f5f6fa", font=("Segoe UI", 10)).pack(anchor="w")
        self.key_entry = tk.Entry(body, font=("Consolas", 12), bd=2, relief="groove")
        self.key_entry.pack(fill="x", pady=(5, 10))
        self.key_entry.bind("<Return>", lambda e: self.verify_key())

        tk.Label(body, text=f"HWID: {self.hwid}", bg="#f5f6fa", fg="#7f8c8d", font=("Segoe UI", 8)).pack(anchor="w")

        self.btn_login = tk.Button(body, text="ĐĂNG NHẬP", command=self.verify_key, 
                                   bg="#44bd32", fg="white", font=("Segoe UI", 10, "bold"), 
                                   bd=0, pady=10, cursor="hand2")
        self.btn_login.pack(fill="x", pady=15)

    def load_stored_key(self):
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r") as f:
                    data = json.load(f)
                    self.key_entry.insert(0, data.get("key", ""))
            except: pass

    def on_closing(self):
        """Thoát toàn bộ tiến trình khi đóng cửa sổ"""
        self.root.destroy()
        sys.exit()

    def verify_key(self):
        key = self.key_entry.get().strip()
        if not key:
            messagebox.showwarning("Thông báo", "Vui lòng nhập License Key!")
            return

        # Vô hiệu hóa nút bấm để tránh spam
        self.btn_login.config(state="disabled", text="ĐANG XÁC THỰC...")
        self.root.update()

        try:
            payload = {"action": "auth", "key": key, "hwid": self.hwid}
            response = requests.post(API_URL, json=payload, timeout=10)
            result = response.text.strip()

            if result == "true":
                with open(LICENSE_FILE, "w") as f:
                    json.dump({"key": key}, f)
                
                messagebox.showinfo("Thành công", "Xác thực thành công!")
                self.is_authenticated = True
                self.root.destroy()
                return # Thoát hàm ngay sau khi destroy để không chạy tiếp xuống dưới

            elif result == "expired":
                messagebox.showerror("Lỗi", "Mã của bạn đã hết hạn sử dụng!")
            elif result == "wrong_hwid":
                messagebox.showerror("Lỗi", "Mã này đã được kích hoạt cho máy khác!")
            elif result == "invalid_key":
                messagebox.showerror("Lỗi", "Mã kích hoạt không đúng!")
            else:
                messagebox.showerror("Lỗi", "Phản hồi từ máy chủ không hợp lệ.")
            
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", "Không thể kết nối đến máy chủ xác thực.")
        
        # Sửa lỗi crash: Chỉ cập nhật lại nút nếu cửa sổ vẫn tồn tại (đăng nhập thất bại)
        try:
            if self.root.winfo_exists():
                self.btn_login.config(state="normal", text="ĐĂNG NHẬP")
        except:
            pass

def run_authentication():
    app = AuthGUI()
    app.root.mainloop()
    # Sau khi mainloop kết thúc (do root.destroy() khi thành công 
    # hoặc người dùng đóng cửa sổ)
    if app.is_authenticated:
        return True
    else:
        # Nếu không xác thực thành công mà cửa sổ đóng thì thoát hẳn
        return False
