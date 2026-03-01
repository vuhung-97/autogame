import tkinter as tk
from tkinter import ttk, messagebox
import requests
import random
import string
from dotenv import load_dotenv
import os

load_dotenv()

# Cấu hình
API_URL = os.getenv("KEY_AUTH")

class AdminTool:
    def __init__(self, root):
        self.root = root
        self.root.title("QUẢN TRỊ VIÊN - LICENSE MANAGER")
        self.root.geometry("500x600") # Tăng chiều cao để hiện thông tin
        self.root.configure(bg="#f0f2f5")

        # --- Giao diện ---
        header = tk.Frame(self.root, bg="#1877f2", height=60)
        header.pack(fill="x")
        tk.Label(header, text="ADMIN CONTROL PANEL", fg="white", bg="#1877f2", 
                 font=("Segoe UI", 14, "bold")).pack(pady=15)

        container = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        container.pack(fill="both", expand=True)

        # Khu vực hiển thị thông tin Key (Chức năng kiểm tra)
        self.info_label = tk.Label(container, text="Thông tin: Chờ kiểm tra...", fg="#4b4f56", 
                                   bg="#ffffff", font=("Segoe UI", 9, "italic"), 
                                   pady=10, relief="solid", bd=1)
        self.info_label.pack(fill="x", pady=(0, 15))

        # Khu vực nhập Key + Nút Random
        tk.Label(container, text="License Key:", bg="#f0f2f5", font=("Segoe UI", 10)).pack(anchor="w")
        
        key_frame = tk.Frame(container, bg="#f0f2f5")
        key_frame.pack(fill="x", pady=(5, 15))
        
        self.key_entry = tk.Entry(key_frame, font=("Consolas", 12), bd=2, relief="groove")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(key_frame, text="🎲 RANDOM", command=self.generate_random_key, 
                  bg="#606770", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=10).pack(side="right")

        # Chọn loại Key (Đã thêm loại Thử)
        tk.Label(container, text="Loại tài khoản (Chỉ dùng khi tạo mới):", bg="#f0f2f5", font=("Segoe UI", 10)).pack(anchor="w")
        self.type_var = tk.StringVar(value="tháng")
        type_frame = tk.Frame(container, bg="#f0f2f5")
        type_frame.pack(fill="x", pady=5)
        tk.Radiobutton(type_frame, text="Thử (2 ngày)", variable=self.type_var, value="thử", bg="#f0f2f5").pack(side="left", padx=5)
        tk.Radiobutton(type_frame, text="Theo Tháng", variable=self.type_var, value="tháng", bg="#f0f2f5").pack(side="left", padx=5)
        tk.Radiobutton(type_frame, text="Vĩnh Viễn", variable=self.type_var, value="vĩnh viễn", bg="#f0f2f5").pack(side="left", padx=5)

        # Nút chức năng
        btn_frame = tk.Frame(container, bg="#f0f2f5")
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="🔍 KIỂM TRA THÔNG TIN KEY", command=self.check_key, 
                  bg="#606770", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=5)

        tk.Button(btn_frame, text="➕ XÁC NHẬN TẠO MỚI", command=self.create_key, 
                  bg="#42b72a", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=5)
        
        tk.Button(btn_frame, text="🔄 RESET KEY (HWID & DATE)", command=self.reset_key, 
                  bg="#1877f2", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=5)
        
        tk.Button(btn_frame, text="🗑️ XÓA KEY KHỎI BẢNG", command=self.delete_key, 
                  bg="#fa3e3e", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=5)

    def generate_random_key(self):
        characters = string.ascii_letters + string.digits
        new_key = ''.join(random.choice(characters) for _ in range(10))
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, new_key)

    def send_request(self, payload):
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            return response.text
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối Server: {e}")
            return None

    def check_key(self):
        """Tách chuỗi từ API bằng dấu | và hiển thị thành 4 dòng"""
        key = self.key_entry.get().strip()
        if not key: 
            return messagebox.showwarning("Cảnh báo", "Vui lòng nhập Key cần kiểm tra")
        
        res_text = self.send_request({"action": "check", "key": key})
        
        if res_text:
            # 1. Tách chuỗi thành danh sách dựa trên dấu |
            # Ví dụ: ["Loại: thử ", " Trạng thái: Đang hoạt động ", ...]
            parts = res_text.split('|')
            
            # 2. Loại bỏ khoảng trắng thừa ở đầu/cuối mỗi phần và nối lại bằng dấu xuống dòng
            # strip() giúp xóa các khoảng cách dư thừa để văn bản thẳng hàng
            formatted_text = "\n".join([part.strip() for part in parts])
            
            # 3. Cập nhật lên giao diện
            self.info_label.config(
                text=formatted_text, 
                fg="#1c1e21", 
                font=("Segoe UI", 9, "bold"),
                justify="left",   # Căn lề trái cho các dòng
                anchor="w",       # Đẩy văn bản sát lề trái khung
                padx=10
            )

    def create_key(self):
        key = self.key_entry.get().strip()
        if not key: return messagebox.showwarning("Cảnh báo", "Vui lòng nhập hoặc tạo Key")
        res = self.send_request({"action": "create", "key": key, "type": self.type_var.get()})
        if res: messagebox.showinfo("Thông báo", res)

    def reset_key(self):
        key = self.key_entry.get().strip()
        if not key: return messagebox.showwarning("Cảnh báo", "Vui lòng nhập Key")
        if messagebox.askyesno("Xác nhận", f"Bạn có muốn reset HWID và Ngày cho key {key}?"):
            res = self.send_request({"action": "reset", "key": key})
            if res: messagebox.showinfo("Thông báo", res)

    def delete_key(self):
        key = self.key_entry.get().strip()
        if not key: return messagebox.showwarning("Cảnh báo", "Vui lòng nhập Key")
        if messagebox.askyesno("Xác nhận", f"XÓA VĨNH VIỄN key {key}?"):
            res = self.send_request({"action": "delete", "key": key})
            if res: messagebox.showinfo("Thông báo", res)

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminTool(root)
    root.mainloop()