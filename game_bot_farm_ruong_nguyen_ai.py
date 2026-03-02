import socket
import subprocess
import time
import threading
import os
import cv2
import numpy as np
from ppadb.client import Client as AdbClient
import sys

from ultralytics import YOLO

# --- HÀM HỖ TRỢ ĐƯỜNG DẪN TÀI NGUYÊN ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Cấu hình ADB ---
ADB_HOST = "127.0.0.1"
ADB_PORT = 5037
MAX_MAP = 2

#kiểu dữ liệu point
class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

P_ATTACK = point(364, 1186)
P_LEFT = point(187, 522)
P_RIGHT = point(518, 522)
P_TOP = point(378, 78)
P_AUTO = point(650, 1186)
P_AUTO_ATTACK = point(360, 1060)
P_EXIT = point(60, 1240)
P_ACCEPT = point(483, 777)

# Định nghĩa các đường dẫn ảnh mẫu (GIỮ NGUYÊN)
IMG_TEMPLATES = {
    "ATTACK": "khieu_chien.png",
    "RUONG_NGUYEN": ["ruong_nguyen_1.png", "ruong_nguyen_2.png"],
    "AUTO_KHIEU_CHIEN": ["auto_khieu_chien.png","auto_khieu_chien_1.png"],
}

class GameAutoBot:
    def __init__(self, log_callback, img_callback=None):
        self.is_running = False
        self.selected_devices = {}
        self.mode_to_tien = False
        self.log_callback = log_callback
        self.img_callback = img_callback  # Thêm callback ảnh
        self.count = 0
        
        # --- KHỞI CHẠY AI KHI BẮT ĐẦU ---
        try:
            # Tải model AI từ file best.pt
            self.model = YOLO(resource_path('best.pt')) 
            self.log("HỆ THỐNG: Đã tải thành công não bộ AI (best.pt)")
        except Exception as e:
            self.log(f"LỖI KHỞI CHẠY AI: {e}")
            self.model = None

    def callback_img(self, screen_img):
        if self.img_callback:
            self.img_callback(screen_img)
        
    
    def log(self, msg, window_name="Bot"):
        if self.log_callback:
            self.log_callback(msg, window_name)

    def refresh_devices(self):
        """Chỉ sử dụng client.devices() nhưng có cơ chế tự làm mới Server"""
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            # 2. Chỉ dùng lệnh lấy thiết bị mặc định
            client = AdbClient(host=ADB_HOST, port=ADB_PORT)
            all_devices = client.devices()
            
            active = []
            for device in all_devices:
                serial = device.serial
                state = device.get_state()
                
                # 3. Lọc bỏ thiết bị lỗi/offline để danh sách UI luôn sạch sẽ
                if state == "device":
                    active.append(device)
                    self.log(f"Tìm thấy thiết bị: {serial}")
                else:
                    # Ngắt kết nối các thiết bị treo để tránh làm nặng danh sách
                    subprocess.run(f"adb disconnect {serial}", shell=True, capture_output=True, startupinfo=startupinfo)
            
            return active
        except Exception as e:
            self.log(f"Lỗi ADB: {e}")
            return []

    # --- CÁC HÀM THAO TÁC (CẬP NHẬT LOG) ---
    def adb_screenshot(self, device):
        try:
            result = device.screencap()
            return cv2.imdecode(np.frombuffer(result, np.uint8), cv2.IMREAD_COLOR)
        except:
            return None

    def adb_click(self, device, x, y):
        # Tọa độ tap được hiển thị chi tiết để debug
        device.shell(f"input tap {int(x)} {int(y)}")

    def get_roi_by_frames(self, w_scr, h_scr, start_frame, num_frames=1):
        h_step = h_scr // 10
        x1, y1 = 0, (start_frame - 1) * h_step
        x2, y2 = w_scr, y1 + (num_frames * h_step)
        return (x1, y1, x2, min(y2, h_scr))

    def safe_locate(self, img_path, screen_img, conf=0.8, area=None):
        if area:
            search_img = screen_img[area[1]:area[3], area[0]:area[2]]
        else:
            search_img = screen_img
        
        full_path = resource_path(img_path)
        if not os.path.exists(full_path): 
            self.log(f"LỖI: File ảnh không tồn tại: {img_path}")
            return False
            
        template = cv2.imread(full_path)
        if template is None: return False
        res = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        # self.log(f"Debug: max_val={cv2.minMaxLoc(res)[1]:.4f} for {img_path}")
        return cv2.minMaxLoc(res)[1] >= conf

    # --- LOGIC XỬ LÝ ---
    # Hàm gọi model
    def predict(self, screen):
        if self.model is None: return []
        return self.model.predict(
            screen, 
            conf=0.5, 
            imgsz=1280, 
            verbose=False,
            stream=False
        )

    def find_stars_and_pos(self, screen, side):
        results = self.predict(screen)  # Chạy dự đoán để cập nhật results
        mid_x = screen.shape[1] // 2
        best_star = 0
        # best_pos = None

        for r in results:
            for box in r.boxes:
                label = self.model.names[int(box.cls[0])] 
                coords = box.xyxy[0].tolist() 
                center_x = (coords[0] + coords[2]) / 2
                center_y = (coords[1] + coords[3]) / 2

                # Lọc theo phía TRÁI hoặc PHẢI
                if (side == "left" and center_x < mid_x) or (side == "right" and center_x >= mid_x):
                    stars = 0
                    try:
                        if 'd' in label:
                            stars = int(label.split('-')[-1]) # Tách số từ 'd-5'
                    except:
                        stars = 0
                    
                    if stars > best_star:
                        best_star = stars
                        # best_pos = (int(center_x), int(center_y))
        return best_star #, best_pos

    def check_battle_status(self, device, screen, name):
        vung = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 2, 4)

        if self.safe_locate('chien_thang.png', screen, conf=0.5, area=vung):
            self.count += 1
            self.log("KẾT QUẢ: CHIẾN THẮNG!", name)
            self.adb_click(device, P_TOP.x, P_TOP.y)
            time.sleep(2); return True
        
        if self.safe_locate('that_bai.png', screen, conf=0.7, area=vung):
            self.log("KẾT QUẢ: THẤT BẠI!", name)
            self.adb_click(device, P_TOP.x, P_TOP.y)
            time.sleep(2); return True
        
        return False

    def find_ruong_nguyen(self, screen):
        results = self.predict(screen)
        if not results:
            return False

        for r in results:
            if not hasattr(r, "boxes") or r.boxes is None:
                continue

            for box in r.boxes:
                if box.cls is None or len(box.cls) == 0:
                    continue

                label = self.model.names[int(box.cls[0])]
                if label == 'r':
                    return True

        return False

    # hàm tìm cửa
    def handle_selection_logic(self, device, screen, name, map_count, has_found_curse):
        # trả ra map_count, có bấm thoát hay không, và có tìm thấy rương nguyền hay không
        s_l = self.find_stars_and_pos(screen, "left")
        s_r = self.find_stars_and_pos(screen, "right")
         
        if map_count >= MAX_MAP and not has_found_curse:
            self.log(">> Không thấy rương nguyền <<", name)
            self.adb_click(device, P_EXIT.x, P_EXIT.y)
            time.sleep(1)
            self.adb_click(device, P_ACCEPT.x, P_ACCEPT.y)
            time.sleep(1.5)
            return map_count, True, False #trả lại map_count chứ ko phải reset
        
        if s_l > 0 or s_r > 0:
        #     self.log(f"Sao trái = {s_l}, Sao phải = {s_r}", name)
            map_count += 1
                
            if map_count == MAX_MAP:
                # self.log("Chế độ Rương Nguyền: Đang ở map 2.", name)
                time.sleep(1.5) # tăng thời gian đợi từ 1.0 => 1.5
                for i in range(5):
                    screen = self.adb_screenshot(device)
                    #self.callback_img(screen)  # Gửi ảnh về giao diện mỗi lần chụp
                    if self.find_ruong_nguyen(screen):
                        self.log(">> PHÁT HIỆN RƯƠNG NGUYỀN <<", name)
                        return map_count, False, True
                    time.sleep(0.5) # tăng thời gian đợi từ 0.3=>0.5
               

            time.sleep(1); 
            return map_count, False, has_found_curse
        return map_count, False, has_found_curse

    def bot_worker(self, device, name):
        self.log(f"LUỒNG MỚI: Bắt đầu hoạt động trên {name}", name)
        map_count, has_found_curse = 0, False 
        idle_count = 0
        MAX_IDLE = 100 

        while self.is_running:
            try:
                screen = self.adb_screenshot(device)
                if screen is None:
                    idle_count += 1
                    if idle_count >= MAX_IDLE:
                        self.log(f"LỖI KẾT NỐI: Không nhận được tín hiệu từ {name}. Dừng Auto.", name)
                        break
                    time.sleep(2)
                    continue

                h_scr, w_scr = screen.shape[:2]

                # 2. KIỂM TRA CHIẾN THẮNG/THẤT BẠI
                if self.check_battle_status(device, screen, name):
                    idle_count = 0
                    map_count, has_found_curse = 1, False
                    continue

                # 3. KIỂM TRA KHIÊU CHIẾN
                v_atk = self.get_roi_by_frames(w_scr, h_scr, 9, 2)
                if self.safe_locate('khieu_chien.png', screen, conf=0.6, area=v_atk):
                    self.log(f"KHIÊU CHIẾN: Rương nguyền {self.count} lần")
                    idle_count = 0
                    self.adb_click(device, P_AUTO.x, P_AUTO.y)
                    time.sleep(1)
                    screen = self.adb_screenshot(device)
                    v_atk_confirm = self.get_roi_by_frames(w_scr, h_scr, 8, 3)
                    # img = screen[v_atk_confirm[1]:v_atk_confirm[3], v_atk_confirm[0]:v_atk_confirm[2]]
                    # self.callback_img(img)
                    for img in IMG_TEMPLATES["AUTO_KHIEU_CHIEN"]:
                        if self.safe_locate(img, screen, conf=0.8, area=v_atk_confirm):
                            self.adb_click(device, P_AUTO_ATTACK.x, P_AUTO_ATTACK.y)
                    map_count, has_found_curse = 1, False
                    time.sleep(1)
                    # Gửi ảnh về giao diện khi phát hiện mục tiêu
                    # self.callback_img(screen)
                    continue

                # 4. LOGIC CHỌN ĐƯỜNG ĐI
                old_map_count = map_count
                map_count, is_exited, has_found_curse = self.handle_selection_logic(device, screen, name, map_count, has_found_curse)

                # Nếu map_count thay đổi hoặc bấm thoát, tức là bot đang hoạt động
                if map_count != old_map_count:
                    idle_count = 0
                    # Gửi ảnh về giao diện khi phát hiện mục tiêu
                    # self.callback_img(screen)
                    continue

                idle_count += 1
                if idle_count >= MAX_IDLE:
                    self.log(f"LỖI KẾT NỐI: Thiết bị {name} không phản hồi quá lâu!", name)
                    break

            except Exception as e:
                self.log(f"LỖI HỆ THỐNG: {e}", name)
                break
            time.sleep(0.5)

    def start(self, devices_to_run, is_to_tien=False):
        self.is_running = True
        self.mode_to_tien = is_to_tien 
        for serial, device in devices_to_run.items():
            threading.Thread(target=self.bot_worker, args=(device, serial), daemon=True).start()

    def stop(self):
        self.is_running = False
        self.log("Đã gửi lệnh dừng máy.")