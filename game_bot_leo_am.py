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
TIME_SLEEP = 4
# Định nghĩa các đường dẫn ảnh mẫu (GIỮ NGUYÊN)
IMG_TEMPLATES = {
    "ATTACK": "khieu_chien.png",
    "TUI": "toi_am_nang.png",
    "RETURN": "thoat.png",
    "DEL_EQUIP": "xac_nhan_tach.png",
    "HOI_SINH": "hoi_sinh.png",
    "TACH": "tach.png",
    "XAC_NHAN": "xac_nhan.png",
    "XAC_NHAN_THOAT": "xac_nhan_thoat.png",
    "TO_TIEN": ["to_tien_1.png", "to_tien_2.png"],
    "SET_NGUYEN_SO": "set_nguyen_so.png",
}

CHON_TRANGBI = [
    "captrangbi/thuong.png", "captrangbi/tot.png", "captrangbi/hiem.png",
    "captrangbi/truyenthuyet.png", "captrangbi/botrangbi.png",
    "captrangbi/truyenthuyetvienco.png", "captrangbi/botrangbivienco.png",
    "captrangbi/truyenthuyetthaico.png", "captrangbi/botrangbithaico.png",
]

LEVEL_NAMES = [
    "Thường", "Tốt", "Hiếm", "Truyền thuyết", "Bộ trang bị",
    "TT Viễn cổ", "Bộ Viễn cổ", "TT Thái cổ", "Bộ Thái cổ"
]

class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

P_LEFT = point(187, 522)
P_RIGHT = point(518, 522)
TAP_POINT = point(100, 100)

def start_adb_server():
    adb_path = resource_path("adb.exe")

    # kiểm tra port 5037 đã mở chưa
    try:
        with socket.create_connection(("127.0.0.1", 5037), timeout=1):
            return True
    except:
        pass

    # nếu chưa mở thì start
    subprocess.run([adb_path, "start-server"], capture_output=True)

    # đợi port mở
    time.sleep(3)
    for _ in range(10):
        try:
            with socket.create_connection(("127.0.0.1", 5037), timeout=1):
                print("ADB đã khởi động")
                return True
        except:
            time.sleep(0.5)

    print("Không thể khởi động ADB")
    return False

class GameAutoBot:
    def __init__(self, log_callback):
        self.is_running = False
        self.selected_devices = {}
        self.current_target_img = CHON_TRANGBI[0]
        self.mode_ruong_nguen = False
        self.log_callback = log_callback 
        if not start_adb_server():
            self.log("Không thể khởi động ADB server")
        # --- KHỞI CHẠY AI KHI BẮT ĐẦU ---
        try:
            # Tải model AI từ file best.pt
            self.model = YOLO(resource_path('best.pt')) 
            self.log("HỆ THỐNG: Đã tải thành công não bộ AI (best.pt)")
        except Exception as e:
            self.log(f"LỖI KHỞI CHẠY AI: {e}")
            self.model = None

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

            adb_path = resource_path("adb.exe")
            for port in range(5555, 5685, 2):
                subprocess.run([adb_path, "connect", f"127.0.0.1:{port}"],
                   capture_output=True)
    
            # 2. Chỉ dùng lệnh lấy thiết bị mặc định như bạn muốn
            try:
                client = AdbClient(host=ADB_HOST, port=ADB_PORT)
                all_devices = client.devices()
            except:
                start_adb_server()
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
                    subprocess.run([adb_path, "disconnect", serial], shell=True, capture_output=True, startupinfo=startupinfo)
            
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
        return cv2.minMaxLoc(res)[1] >= conf

    def locate_center(self, img_path, screen_img, conf=0.8, area=None):
        # Xác định tọa độ gốc để cộng dồn sau khi tìm thấy ảnh trong vùng cắt
        x1, y1 = (area[0], area[1]) if area else (0, 0)
        
        # Cắt vùng ảnh để tìm kiếm
        if area:
            search_img = screen_img[area[1]:area[3], area[0]:area[2]]
        else:
            search_img = screen_img

        full_path = resource_path(img_path)
        if not os.path.exists(full_path):
            self.log(f"LỖI: File ảnh không tồn tại: {img_path}")
            return None
            
        template = cv2.imread(full_path)
        if template is None: return None
        
        h, w = template.shape[:2]
        res = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= conf:
            # Trả về tọa độ tâm
            return (x1 + max_loc[0] + w // 2, y1 + max_loc[1] + h // 2)
        return None

    def adb_click_template(self, device, screen, template_name, action, area=None, conf=0.8):
        pos = self.locate_center(template_name, screen, conf=conf, area=area)
        if pos:
            self.adb_click(device, pos[0], pos[1])
            # self.log(f"Đã click nút '{action}' tại vị trí ({pos[0]}, {pos[1]})", device.serial)
            return True
        return False

    # --- LOGIC XỬ LÝ ---
    def find_stars_and_pos(self, screen, side):
        if self.model is None: return 0, None
        
        results = self.model.predict(screen, conf=0.5, imgsz=1280, verbose=False)
        mid_x = screen.shape[1] // 2
        best_star, best_pos = 0, None

        for r in results:
            for box in r.boxes:
                label = self.model.names[int(box.cls[0])] 
                coords = box.xyxy[0].tolist() 
                center_x = (coords[0] + coords[2]) / 2
                center_y = (coords[1] + coords[3]) / 2

                # Lọc theo phía TRÁI hoặc PHẢI
                if (side == "left" and center_x < mid_x) or (side == "right" and center_x >= mid_x):
                    try:
                        stars = int(label.split('-')[-1]) # Tách số từ 'd-5'
                    except:
                        stars = 0
                    
                    if stars > best_star:
                        best_star = stars
                        best_pos = (int(center_x), int(center_y))
        return best_star, best_pos
    
    def check_hoi_sinh(self, device, screen, name):
        vung = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 5, 3)
        if self.safe_locate('hoi_sinh.png', screen, conf=0.7, area=vung):
            self.log("TRẠNG THÁI: Nhân vật hy sinh. Đang bấm hồi sinh...", name)
            self.adb_click_template(device, screen, IMG_TEMPLATES["HOI_SINH"], "Hồi sinh", area=vung, conf=0.7)
            time.sleep(TIME_SLEEP); return True
        return False

    def check_battle_status(self, device, screen, name):
        vung = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 2, 4)
        if self.safe_locate('chien_thang.png', screen, conf=0.5, area=vung):
            self.log("CHIẾN THẮNG! Đang thoát trận...", name)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(TIME_SLEEP); return True
        if self.safe_locate('that_bai.png', screen, conf=0.7, area=vung):
            self.log("THẤT BẠI! Đang thoát trận...", name)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(TIME_SLEEP); return True
        return False

    # hàm chọn cửa cho ải thường
    def handle_selection_logic(self, device, screen):
        s_l, pos_l = self.find_stars_and_pos(screen, "left")
        s_r, pos_r = self.find_stars_and_pos(screen, "right")
        
        if s_l > 0 or s_r > 0:
            if s_l == 1:
                self.adb_click(device, P_RIGHT.x, P_RIGHT.y)
                return True
            if s_r == 1: 
                self.adb_click(device, P_LEFT.x, P_LEFT.y)
                return True
            if s_l == 2:
                self.adb_click(device, P_RIGHT.x, P_RIGHT.y)
                return True
            if s_r == 2: 
                self.adb_click(device, P_LEFT.x, P_LEFT.y)
                return True
            if s_l >= s_r and pos_l is not None: 
                self.adb_click(device, pos_l[0], pos_l[1])
            elif pos_r is not None: 
                self.adb_click(device, pos_r[0], pos_r[1])   
            time.sleep(TIME_SLEEP)
            return True
        return False

    def bot_worker(self, device, name):
        self.log(f"LUỒNG MỚI: Bắt đầu hoạt động trên {name}", name)
        
        # Biến đếm số lần duyệt vòng lặp mà không tìm thấy bất kỳ hành động nào
        idle_count = 0
        # Ngưỡng dừng: 60 lần liên tiếp (~3 phút) không thấy ảnh sẽ báo lỗi và dừng
        MAX_IDLE = 60 

        while self.is_running:
            try:
                screen = self.adb_screenshot(device)
                
                # Trường hợp không nhận được ảnh (Mất kết nối ADB hoặc thiết bị đơ)
                if screen is None:
                    idle_count += 1
                    if idle_count >= MAX_IDLE:
                        self.log(f"LỖI KẾT NỐI: Không nhận được tín hiệu từ {name}. Dừng Auto.", name)
                        break
                    time.sleep(TIME_SLEEP)
                    continue

                h_scr, w_scr = screen.shape[:2]
                vung_giua = self.get_roi_by_frames(w_scr, h_scr, 4, 4)

                # 1. KIỂM TRA ĐẦY TÚI
                if self.safe_locate('toi_am_nang.png', screen, conf=0.7, area=vung_giua):
                    idle_count = 0 # RESET TẠI ĐÂY TRƯỚC KHI CONTINUE
                    self.log("PHÁT HIỆN: Túi đồ đã đầy!", name)
                    self.adb_click_template(device, screen, IMG_TEMPLATES["TUI"], "Mở túi", area=vung_giua, conf=0.7)
                    time.sleep(TIME_SLEEP)
                    
                    screen = self.adb_screenshot(device)
                    v_to_tien = self.get_roi_by_frames(w_scr, h_scr, 6, 3)
                    totien = False
                    img = None
                    for tt_img in IMG_TEMPLATES["TO_TIEN"]:
                        if self.safe_locate(tt_img, screen, conf=0.7, area=v_to_tien):
                            img = tt_img
                            totien = True
                            break
                    
                    if totien:
                        self.adb_click_template(device, screen, img, "Tổ tiên", area=v_to_tien, conf=0.7)
                        screen = self.adb_screenshot(device)
                        self.adb_click_template(device, screen, IMG_TEMPLATES["SET_NGUYEN_SO"], "Set nguyên sơ", area=v_to_tien, conf=0.7)
                        
                    time.sleep(TIME_SLEEP)
                        
                    screen = self.adb_screenshot(device)
                    self.adb_click_template(device, screen, IMG_TEMPLATES["TACH"], "Bấm Nút Tách", area=vung_giua)
                    time.sleep(TIME_SLEEP)
                    
                    s_tui = self.adb_screenshot(device)
                    v_chon = self.get_roi_by_frames(w_scr, h_scr, 4, 3)
                    # self.log(f"Đang tìm trang bị: {self.current_target_img}")
                    t_pos = self.locate_center(self.current_target_img, s_tui, conf=0.9, area=v_chon)
                    if t_pos:
                        self.adb_click(device, t_pos[0], t_pos[1]); time.sleep(TIME_SLEEP)
                        s_after = self.adb_screenshot(device)
                        self.adb_click_template(device, s_after, IMG_TEMPLATES["XAC_NHAN"], "Xác nhận chọn", area=vung_giua, conf=0.7)
                        time.sleep(TIME_SLEEP)
                        s_after = self.adb_screenshot(device)
                        self.adb_click_template(device, s_after, IMG_TEMPLATES["DEL_EQUIP"], "Tách", area=vung_giua)
                        time.sleep(TIME_SLEEP)
                        s_after = self.adb_screenshot(device)
                        self.adb_click_template(device, s_after, IMG_TEMPLATES["XAC_NHAN_THOAT"], "Xác nhận tách", area=vung_giua, conf=0.7)
                        time.sleep(TIME_SLEEP)
                        self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                        time.sleep(TIME_SLEEP)
                        s_exit = self.adb_screenshot(device)
                        v_day = self.get_roi_by_frames(w_scr, h_scr, 10, 1)
                        self.adb_click_template(device, s_exit, IMG_TEMPLATES["RETURN"], "Đóng túi đồ", area=v_day)
                        time.sleep(TIME_SLEEP)
                    else:
                        v_thoat = self.get_roi_by_frames(w_scr, h_scr, 10, 1)
                        self.adb_click_template(device, screen, IMG_TEMPLATES["RETURN"], "Thoát túi", area=v_thoat)
                        time.sleep(TIME_SLEEP)
                    continue 

                # 2. KIỂM TRA CHIẾN THẮNG/THẤT BẠI
                if self.check_battle_status(device, screen, name):
                    idle_count = 0 # RESET TẠI ĐÂY
                    continue
                    
                # 3. KIỂM TRA KHIÊU CHIẾN
                v_atk = self.get_roi_by_frames(w_scr, h_scr, 9, 2)
                if self.safe_locate('khieu_chien.png', screen, conf=0.7, area=v_atk):
                    idle_count = 0 # RESET TẠI ĐÂY
                    self.adb_click_template(device, screen, IMG_TEMPLATES["ATTACK"], "Nút KHIÊU CHIẾN", area=v_atk, conf=0.7)
                    time.sleep(TIME_SLEEP); continue
                    
                # 4. KIỂM TRA HỒI SINH
                if self.check_hoi_sinh(device, screen, name):
                    idle_count = 0 # RESET TẠI ĐÂY
                    continue
                
                # 5. LOGIC CHỌN ĐƯỜNG ĐI
                self.handle_selection_logic(device, screen)
                
                # --- NẾU KHÔNG RƠI VÀO CÁC IF TRÊN THÌ TĂNG BIẾN ĐỢI ---
                idle_count += 1
                if idle_count >= MAX_IDLE:
                    self.log(f"LỖI KẾT NỐI: Thiết bị {name} không phản hồi quá lâu!", name)
                    break

            except Exception as e:
                self.log(f"LỖI HỆ THỐNG: {e}", name)
                break
            time.sleep(TIME_SLEEP)
        
        self.log(f"--- ĐÃ DỪNG THIẾT BỊ {name} ---", name)

    def start(self, devices_to_run, is_ruong_nguyen=False):
        self.is_running = True
        self.mode_ruong_nguyen = is_ruong_nguyen
        for serial, device in devices_to_run.items():
            threading.Thread(target=self.bot_worker, args=(device, serial), daemon=True).start()

    def stop(self):
        self.is_running = False
        self.log("Đã gửi lệnh dừng tới tất cả các máy.")