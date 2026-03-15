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
TIME_SLEEP_SHORT = 2
# Định nghĩa các đường dẫn ảnh mẫu (GIỮ NGUYÊN)
IMG_TEMPLATES = {
    "ATTACK": "khieu_chien.png",
    "MO_TUI": "toi_am_nang.png",
    "RETURN": "thoat.png",
    "DEL_EQUIP": "xac_nhan_tach.png",
    "HOI_SINH": "hoi_sinh.png",
    "TACH": "tach.png",
    "XAC_NHAN": "xac_nhan.png",
    "XAC_NHAN_THOAT": "xac_nhan_thoat.png",
    "TO_TIEN": ["to_tien_1.png", "to_tien_2.png"],
    "SET_NGUYEN_SO": "set_nguyen_so.png",
    "RUONG_NGUYEN": ["ruong_nguyen_1.png", "ruong_nguyen_2.png", "ruong_nguyen_3.png"],
    "CUA_RUONG_NGUYEN": ["star_4_1.png", "star_4_2.png", "star_4_3.png"],
    "CHIEN_THANG": "chien_thang.png",
    "THAT_BAI": "that_bai.png",
    "KHIEU_CHIEN": "khieu_chien.png",
    "HOI_SINH": "hoi_sinh.png",
    "THAY_THE": "thay_the.png",
    "NUT_NHIEM_VU": "nv_hang_ngay/nut_nhiem_vu.png",
    "NHIEM_VU": "nv_hang_ngay/nhiem_vu.png",
    "CHIEU_MO_BUA": "nv_hang_ngay/chieu_mo_bua.png",
    "CONG_SU": "nv_hang_ngay/cong_su.png",
    "CHINH_PHAT_THU_LINH": "nv_hang_ngay/chinh_phat_thu_linh.png",
    "NONG_TRAI_HON_DON": "nv_hang_ngay/nong_trai_hon_don.png",
    "THU_VIEN": "nv_hang_ngay/thu_vien.png",
    "CHUC_MUNG_NHAN": "nv_hang_ngay/chuc_mung_nhan.png",
    "THE_BI_AN": "nv_hang_ngay/the_bi_an.png",
    "TUONG": ["nv_hang_ngay/tuong_be.png", "nv_hang_ngay/tuong_vua.png", "nv_hang_ngay/tuong_lon.png"],
    "CUA_QUA_MAN_MO_THE": "nv_hang_ngay/cua_qua_man_mo_the.png",
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
P_EXIT = point(60, 1240)
P_ACCEPT = point(483, 777)
P_RUONG_TO_TIEN = point(250, 830)
P_RUONG_NGUYEN_SO = point(258, 872)

P_NHAN_QUA = point(272, 1130)

TAP_POINT = point(350, 10)

# nhiệm vụ hàng ngày
P_DOANH_TRAI = point(80, 1230)
P_KY_NANG = point(210, 1230)
P_SANH = point(360, 1230)
P_MAO_HIEM = point(500, 1230)
P_TRAN = point(650, 1230)
# nhiệm vụ chiêu mộ cộng sự
P_CONG_SU = point(350, 170)
P_CHIEU_MO = point(410, 1230)
P_CHIEU_MO_LAM_MOI = point(510, 1000)
P_CHIEU_MO_1 = point(130, 910)
P_CHIEU_MO_2 = point(360, 910)
P_CHIEU_MO_3 = point(590, 910)
# nhiệm vụ chiêu mộ bùa
P_CHIEU_MO_BUA = point(630, 990)
P_CHIEU_MO_BUA_3_LAN = point(360, 1020)
# nhiệm vụ chinh phạt thủ lĩnh
P_CHINH_PHAT_THU_LINH = point(200, 600)
P_VAO_CHINH_PHAT = point(310, 1040)
P_XAC_NHAN_CHINH_PHAT_NHANH = point(480, 777)
P_CHINH_PHAT_NHANH = point(460, 1040)
#TAP POINT 2 LẦN
# nhiệm vụ nông trại hỗn độn
P_NONG_TRAI_HON_DON = point(220, 250)
P_QUET = point(490, 1040)
P_XAC_NHAN = point(480, 770)
# TAP POINT 2 LẦN
# nhiệm vụ thư viện
P_THU_VIEN = point(110, 800)
P_HIEN_GIA = point(650, 1230)
P_CHON_HIEN_GIA = point(200, 330)
P_QUA = point(560, 960) #tặng 3 lần
P_THE = point(134, 364)
X_TANG = 114
Y_TANG = 114
# về sảnh chính nhận quà
# bấm nút sảnh 30s, sau đó tìm nút nv
P_DUNG_DANH_QUAI = point(210, 177)
P_NV = point(645, 170)
P_NV_HANG_NGAY = point(640, 390)
P_HOAN_THANH_NV = point(550, 470) # 10 lần
P_NHAN_VANG = point(420, 300)
# TAP POINT 2 LẦN

class GameAutoBot:
    def __init__(self, log_callback, img_callback=None):
        self.is_running = False
        self.selected_devices = {}
        self.current_target_img = CHON_TRANGBI[0]
        self.mode_ruong_nguyen = False
        self.log_callback = log_callback 
        self.img_callback = img_callback  # Thêm callback ảnh
        
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

    def callback_img(self, screen_img):
        if self.img_callback:
            self.img_callback(screen_img)
        
    def refresh_devices(self):
        """Chỉ sử dụng client.devices() nhưng có cơ chế tự làm mới Server"""
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            # 2. Chỉ dùng lệnh lấy thiết bị mặc định như bạn muốn
            client = AdbClient(host=ADB_HOST, port=ADB_PORT)
            all_devices = client.devices()
            
            active = []
            for device in all_devices:
                serial = device.serial
                try:
                    state = device.get_state()
                except Exception:
                    # thiết bị lỗi / zombie
                    subprocess.run(f"adb disconnect {serial}", shell=True,
                                capture_output=True, startupinfo=startupinfo)
                    continue
                
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

    # hàm gọi AI
    def predict(self, screen):
        if self.model is None: return []
        return self.model.predict(
            screen, 
            conf=0.5, 
            imgsz=1280, 
            verbose=False,
            stream=False
            )
    
    # --- LOGIC XỬ LÝ ---
    def find_stars_and_pos(self, screen, side):
        results = self.predict(screen)
        if not results: return 0, None
        
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
                    stars = 0
                    try:
                        if 'd' in label:
                            stars = int(label.split('-')[-1]) # Tách số từ 'd-..'
                    except:
                        stars = 0
                    
                    if stars > best_star:
                        best_star = stars
                        best_pos = (int(center_x), int(center_y))
        return best_star, best_pos
    
    def check_hoi_sinh(self, device, screen, name):
        vung = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 5, 3)
        if self.adb_click_template(device, screen, IMG_TEMPLATES["HOI_SINH"], "Hồi sinh", area=vung, conf=0.7):
            self.log("TRẠNG THÁI: Nhân vật hy sinh. Đang bấm hồi sinh...", name)
            time.sleep(self.time_sleep); return True
        return False

    def check_battle_status(self, device, screen, name):
        vung = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 2, 4)

        if self.safe_locate(IMG_TEMPLATES["CHIEN_THANG"], screen, conf=0.5, area=vung):
            self.log("CHIẾN THẮNG! Đang thoát trận...", name)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep); return True
        
        if self.safe_locate(IMG_TEMPLATES["THAT_BAI"], screen, conf=0.7, area=vung):
            self.log("THẤT BẠI! Đang thoát trận...", name)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep); return True
        return False

    # hàm tìm rương
    def handle_find_ruong(self, screen):
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

    # hàm chọn cửa cho ải thường
    def handle_selection_logic(self, device, screen, name, map_count, found_ruong = False):
        # return về đã click và found_ruong
        s_l, pos_l = self.find_stars_and_pos(screen, "left")
        s_r, pos_r = self.find_stars_and_pos(screen, "right")
        if map_count == MAX_MAP and self.mode_ruong_nguyen and not found_ruong:
            for i in range(5): # Tăng số lần kiểm tra để tìm rương nguyền
                self.callback_img(screen)
                screen = self.adb_screenshot(device)
                if self.handle_find_ruong(screen):
                    self.log(">> Đã  thấy Rương Nguyền!", name)
                    found_ruong = True
                    break
                time.sleep(0.5)

            # Nếu không thấy rương thì thoát
            if not found_ruong:
                self.adb_click(device, P_EXIT.x, P_EXIT.y)
                time.sleep(TIME_SLEEP_SHORT)
                self.adb_click(device, P_ACCEPT.x, P_ACCEPT.y)
                return True, found_ruong

        if s_l > 0 or s_r > 0:
            if map_count >= 2 and self.mode_ruong_nguyen and not found_ruong:
                self.log(">> Map 2 không thấy Rương nguyền! <<", name)
                time.sleep(TIME_SLEEP_SHORT)
                self.adb_click(device, P_EXIT.x, P_EXIT.y)
                time.sleep(TIME_SLEEP_SHORT)
                self.adb_click(device, P_ACCEPT.x, P_ACCEPT.y)
                return True, found_ruong

            if s_l == 4:
                self.adb_click(device, P_LEFT.x, P_LEFT.y)
                return True, found_ruong
            if s_r == 4:
                self.adb_click(device, P_RIGHT.x, P_RIGHT.y)
                return True, found_ruong
            if s_l == 1:
                self.adb_click(device, P_RIGHT.x, P_RIGHT.y)
                return True, found_ruong
            if s_r == 1: 
                self.adb_click(device, P_LEFT.x, P_LEFT.y)
                return True, found_ruong
            if s_l == 2:
                self.adb_click(device, P_RIGHT.x, P_RIGHT.y)
                return True, found_ruong
            if s_r == 2: 
                self.adb_click(device, P_LEFT.x, P_LEFT.y)
                return True, found_ruong
            
            if s_l >= s_r and pos_l is not None: 
                self.adb_click(device, pos_l[0], pos_l[1])
            elif pos_r is not None: 
                self.adb_click(device, pos_r[0], pos_r[1]) 
            return True, found_ruong
        return False, found_ruong

    def start(self, devices_to_run, is_ruong_nguyen=False):
        self.is_running = True
        self.mode_ruong_nguyen = is_ruong_nguyen
        self.time_sleep = TIME_SLEEP if not is_ruong_nguyen else TIME_SLEEP_SHORT
        for serial, device in devices_to_run.items():
            threading.Thread(target=self.bot_worker, args=(device, serial), daemon=True).start()

    def bot_worker(self, device, name):
        self.log(f"LUỒNG MỚI: Bắt đầu hoạt động trên {name}", name)
        
        map_count, found_ruong = 1, False 
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
                if self.adb_click_template(device, screen, IMG_TEMPLATES["MO_TUI"], "Mở túi", area=vung_giua, conf=0.8):
                    idle_count = 0 # RESET TẠI ĐÂY TRƯỚC KHI CONTINUE
                    self.log("PHÁT HIỆN: Túi đồ đã đầy!", name)
                    time.sleep(TIME_SLEEP)

                    self.adb_click(device, P_RUONG_TO_TIEN.x, P_RUONG_TO_TIEN.y);
                    time.sleep(TIME_SLEEP/2)
                    self.adb_click(device, P_RUONG_NGUYEN_SO.x, P_RUONG_NGUYEN_SO.y);
                    time.sleep(TIME_SLEEP)
                        
                    screen = self.adb_screenshot(device)
                    self.adb_click_template(device, screen, IMG_TEMPLATES["TACH"], "Bấm Nút Tách", area=vung_giua)
                    time.sleep(TIME_SLEEP)
                    
                    s_tui = self.adb_screenshot(device)
                    v_chon = self.get_roi_by_frames(w_scr, h_scr, 4, 3)
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
                if self.adb_click_template(device, screen, IMG_TEMPLATES["ATTACK"], "Nút KHIÊU CHIẾN", area=v_atk, conf=0.6):
                    idle_count = 0 # RESET TẠI ĐÂY                    
                    self.log("KHIÊU CHIẾN!", name)
                    map_count, found_ruong = 1, False
                    time.sleep(self.time_sleep); 
                    continue
                    
                # 4. KIỂM TRA HỒI SINH
                if self.check_hoi_sinh(device, screen, name):
                    idle_count = 0 # RESET TẠI ĐÂY
                    continue

                # 5. LOGIC CHỌN ĐƯỜNG ĐI
                clicked, found_ruong = self.handle_selection_logic(device, screen, name, map_count, found_ruong)
                if clicked:
                    time.sleep(self.time_sleep-0.5)
                    idle_count = 0 # RESET TẠI ĐÂY
                    map_count += 1
                    continue

                # --- NẾU KHÔNG RƠI VÀO CÁC IF TRÊN THÌ TĂNG BIẾN ĐỢI ---
                idle_count += 1
                if idle_count >= MAX_IDLE:
                    self.log(f"LỖI KẾT NỐI: Thiết bị {name} không phản hồi quá lâu!", name)
                    break

            except Exception as e:
                self.log(f"LỖI HỆ THỐNG: {e}", name)
                break
            time.sleep(self.time_sleep)
        
        self.log(f"--- ĐÃ DỪNG THIẾT BỊ {name} ---", name)

    def start_auto_sanh(self, devices_to_run):
        self.is_running = True
        self.time_sleep = TIME_SLEEP
        for serial, device in devices_to_run.items():
            threading.Thread(target=self.bot_nhan_qua_sanh, args=(device, serial), daemon=True).start()

    def bot_nhan_qua_sanh(self, device, name):
        self.log(f"LUỒNG MỚI: Bắt đầu nhận quà sảnh trên {name}", name)
        while self.is_running:
            try:
                screen = self.adb_screenshot(device)
                if screen is None:
                    time.sleep(TIME_SLEEP)
                    continue

                v_sanh = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 5, 6)
                if self.adb_click_template(device, screen, IMG_TEMPLATES["THAY_THE"], "Nhận quà sảnh", area=v_sanh, conf=0.7):
                    self.log("Thay thế đồ!", name)
            except Exception as e:
                self.log(f"LỖI HỆ THỐNG: {e}", name)
                break
            self.adb_click(device, P_NHAN_QUA.x, P_NHAN_QUA.y)
            time.sleep(1)
            self.adb_click(device, P_NHAN_QUA.x, P_NHAN_QUA.y)
            time.sleep(TIME_SLEEP)

    def start_auto_nv(self, devices_to_run):
        self.is_running = True
        self.time_sleep = 2
        for serial, device in devices_to_run.items():
            threading.Thread(target=self.bot_auto_nv, args=(device, serial), daemon=True).start()

    def bot_auto_nv(self, device, name):
        self.log(f"LUỒNG MỚI: Bắt đầu làm nhiệm vụ hàng ngày trên {name}", name)
        try:
            self.chieu_mo_cong_su(device, name, self.is_running)

            self.chieu_mo_bua(device, name, self.is_running)

            self.nong_trai_hon_don(device, name, self.is_running)

            self.chinh_phat_thu_linh(device, name, self.is_running)

            self.thu_vien(device, name, self.is_running)

            self.auto_sanh_chinh(device, name, self.is_running)

            if not self.is_running:
                return
            
        except Exception as e:
            self.log(f"LỖI HỆ THỐNG: {e}", name)
        
        # Dừng luồng của device này sau khi hoàn thành nhiệm vụ
        self.log(f"--- ĐÃ HOÀN THÀNH NHIỆM VỤ HÀNG NGÀY TRÊN {name} ---", name)

    def chieu_mo_bua(self, device, name, isrunning=False):
        # Chiêu mộ bùa
        find_chieu_mo_bua = False
        if isrunning:
            for _ in range(3):
                self.adb_click(device, P_KY_NANG.x, P_KY_NANG.y)
                time.sleep(self.time_sleep*2)
                
                screen = self.adb_screenshot(device)
                if screen is None:
                    time.sleep(self.time_sleep)
                    continue
                
                v_chieu_mo_bua = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 7, 3)

                if self.safe_locate(IMG_TEMPLATES["CHIEU_MO_BUA"], screen, area=v_chieu_mo_bua, conf=0.85):
                    find_chieu_mo_bua = True
                    break
            
            if not find_chieu_mo_bua:
                return
            
            self.adb_click(device, P_CHIEU_MO_BUA.x, P_CHIEU_MO_BUA.y)
            time.sleep(self.time_sleep)

            for _ in range(3):
                time.sleep(self.time_sleep)
                self.adb_click(device, P_CHIEU_MO_BUA_3_LAN.x, P_CHIEU_MO_BUA_3_LAN.y)
                time.sleep(self.time_sleep)
                self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep)
            for _ in range(2):
                self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                time.sleep(self.time_sleep)

    def chieu_mo_cong_su(self, device, name, isrunning=False):
        # Chiêu mộ cộng sự
        if isrunning:
            find_cong_su = False
            for _ in range(3):
                time.sleep(self.time_sleep)
                self.adb_click(device, P_DOANH_TRAI.x, P_DOANH_TRAI.y); 
                time.sleep(self.time_sleep)

                screen = self.adb_screenshot(device)
                if screen is None:
                    time.sleep(self.time_sleep)
                    continue

                v_cong_su = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 1, 3)
                if self.safe_locate(IMG_TEMPLATES["CONG_SU"], screen, area=v_cong_su, conf=0.85):
                    find_cong_su = True
                    break

            if not find_cong_su:
                return
                
            self.adb_click(device, P_CONG_SU.x, P_CONG_SU.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHIEU_MO.x, P_CHIEU_MO.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHIEU_MO_LAM_MOI.x, P_CHIEU_MO_LAM_MOI.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHIEU_MO_1.x, P_CHIEU_MO_1.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHIEU_MO_2.x, P_CHIEU_MO_2.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHIEU_MO_3.x, P_CHIEU_MO_3.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep)
            for _ in range(2):
                self.adb_click(device, P_EXIT.x, P_EXIT.y)
                time.sleep(self.time_sleep)

    def chinh_phat_thu_linh(self, device, name, isrunning=False):
        # Chinh phạt thủ lĩnh
        if isrunning:
            find_chinh_phat = False
            for _ in range(3):
                time.sleep(self.time_sleep)
                self.adb_click(device, P_MAO_HIEM.x, P_MAO_HIEM.y)
                time.sleep(self.time_sleep)
                
                screen = self.adb_screenshot(device)
                if screen is None:
                    time.sleep(self.time_sleep)
                    continue

                v_chinh_phat = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 3, 4)
                if self.safe_locate(IMG_TEMPLATES["CHINH_PHAT_THU_LINH"], screen, area=v_chinh_phat, conf=0.75):
                    find_chinh_phat = True
                    break
            if not find_chinh_phat:
                return

            self.adb_click(device, P_CHINH_PHAT_THU_LINH.x, P_CHINH_PHAT_THU_LINH.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_VAO_CHINH_PHAT.x, P_VAO_CHINH_PHAT.y)

            time_errors = 0
            while (time_errors < 25):
                time.sleep(self.time_sleep)
                screen = self.adb_screenshot(device)
                v_thong_bao = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 3, 3)
                if self.safe_locate(IMG_TEMPLATES["CHUC_MUNG_NHAN"], screen, area=v_thong_bao, conf=0.7):
                    self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                    time.sleep(self.time_sleep)
                    break
                time_errors += 1
            
            for _ in range(4):
                self.adb_click(device, P_CHINH_PHAT_NHANH.x, P_CHINH_PHAT_NHANH.y)
                time.sleep(self.time_sleep)
                self.adb_click(device, P_XAC_NHAN_CHINH_PHAT_NHANH.x, P_XAC_NHAN_CHINH_PHAT_NHANH.y)
                time.sleep(self.time_sleep)
                self.adb_click(device, P_CHINH_PHAT_NHANH.x, P_CHINH_PHAT_NHANH.y)
                time.sleep(self.time_sleep)

            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
            time.sleep(self.time_sleep)       

    def nong_trai_hon_don(self, device, name, isrunning=False):
        # Nông trại hỗn độn
        if isrunning:
            find_nong_trai = False
            for _ in range(3):
                time.sleep(self.time_sleep)
                self.adb_click(device, P_MAO_HIEM.x, P_MAO_HIEM.y)
                time.sleep(self.time_sleep)

                screen = self.adb_screenshot(device)
                v_nong_trai = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 1, 4)
                if self.safe_locate(IMG_TEMPLATES["NONG_TRAI_HON_DON"], screen, area=v_nong_trai, conf=0.75):
                    find_nong_trai = True
                    break
            if not find_nong_trai:
                return

            self.adb_click(device, P_NONG_TRAI_HON_DON.x, P_NONG_TRAI_HON_DON.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_QUET.x, P_QUET.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_XAC_NHAN.x, P_XAC_NHAN.y)
            time.sleep(self.time_sleep)
            for _ in range(2):
                self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                time.sleep(self.time_sleep)

    def thu_vien(self, device, name, isrunning=False):
        # Thư viện
        if isrunning:
            find_thu_vien = False
            for _ in range(3):
                time.sleep(self.time_sleep)
                self.adb_click(device, P_TRAN.x, P_TRAN.y)
                time.sleep(self.time_sleep)

                screen = self.adb_screenshot(device)
                v_thu_vien = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 5, 4)
                if self.safe_locate(IMG_TEMPLATES["THU_VIEN"], screen, area=v_thu_vien, conf=0.85):
                    find_thu_vien = True
                    break
            if not find_thu_vien:
                return

            self.adb_click(device, P_THU_VIEN.x, P_THU_VIEN.y)
            time.sleep(self.time_sleep)

            for _ in range(3):
                screen = self.adb_screenshot(device)
                if screen is None:
                    time.sleep(self.time_sleep)
                    continue
                else:
                    break

            # mở tượng
            for img in IMG_TEMPLATES["TUONG"]:
                pos = self.locate_center(img, screen, conf=0.85)
                if pos:
                    for _ in range(6):
                        self.adb_click(device, pos[0], pos[1])
                        time.sleep(self.time_sleep)

            # qua cửa
            screen = self.adb_screenshot(device)
            pos =  self.locate_center(IMG_TEMPLATES["CUA_QUA_MAN_MO_THE"], screen, conf=0.7)
            if pos: 
                for _ in range(2):
                    self.adb_click(device, pos[0], pos[1])
                    time.sleep(self.time_sleep)
                    
            # mở thẻ
            if self.safe_locate(IMG_TEMPLATES["THE_BI_AN"], screen, conf=0.7, area=v_thu_vien):
                for x in range(5):
                    for y in range(6):
                        self.adb_click(device, P_THE.x + x*X_TANG, P_THE.y + y*Y_TANG)
                        time.sleep(0.7)

            time.sleep(self.time_sleep)
            self.adb_click(device, P_HIEN_GIA.x, P_HIEN_GIA.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_CHON_HIEN_GIA.x, P_CHON_HIEN_GIA.y)
            time.sleep(self.time_sleep*3)
            for _ in range(3):
                self.adb_click(device, P_QUA.x, P_QUA.y)
                time.sleep(self.time_sleep)
            for _ in range(2):
                self.adb_click(device, P_EXIT.x, P_EXIT.y)
                time.sleep(self.time_sleep)

    def auto_sanh_chinh(self, device, name, isrunning=False):
        # Auto ở sảnh chính
        if isrunning:
            self.adb_click(device, P_SANH.x, P_SANH.y)
            time.sleep(self.time_sleep)
            self.adb_click(device, P_SANH.x, P_SANH.y)
            time.sleep(45) # nghỉ 45s để hoàn thành các nhiệm vụ
            while(self.is_running):
                time.sleep(5)
                screen = self.adb_screenshot(device)
                if screen is None:
                    continue

                v_sanh = self.get_roi_by_frames(screen.shape[1], screen.shape[0], 2, 4)
                if self.safe_locate(IMG_TEMPLATES["NUT_NHIEM_VU"], screen, area=v_sanh, conf=0.85):
                    self.adb_click(device, P_DUNG_DANH_QUAI.x, P_DUNG_DANH_QUAI.y)
                    time.sleep(self.time_sleep*3)
                    self.adb_click(device, P_NV.x, P_NV.y)
                    time.sleep(self.time_sleep)
                    screen = self.adb_screenshot(device)
                    if self.adb_click_template(device, screen, IMG_TEMPLATES["NHIEM_VU"], "Nhiệm vụ", area=v_sanh, conf=0.85):
                        time.sleep(self.time_sleep)
                        for i in range(10):
                            self.adb_click(device, P_HOAN_THANH_NV.x, P_HOAN_THANH_NV.y)
                            time.sleep(self.time_sleep)
                            self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                            time.sleep(self.time_sleep)

                        self.adb_click(device, P_NHAN_VANG.x, P_NHAN_VANG.y)
                        time.sleep(self.time_sleep)
                    self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                    time.sleep(self.time_sleep)
                    self.adb_click(device, TAP_POINT.x, TAP_POINT.y)
                    time.sleep(self.time_sleep)
                    break

    def stop(self):
        self.is_running = False
        self.log("Đã gửi lệnh dừng tới tất cả các máy.")