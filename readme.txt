pyarmor gen main.py auth.py game_bot.py



pyinstaller --noconfirm --onedir --windowed `
--name "AutoFarmRuong" `
--add-data "captrangbi;captrangbi" `
--add-data "*.png;." `
--add-data "dist/pyarmor_runtime_000000;pyarmor_runtime_000000" `
--add-data "adb.exe;." `
--add-data "AdbWinApi.dll;." `
--add-data "AdbWinUsbApi.dll;."`
--collect-all "cv2" `
--collect-all "ppadb" `
--collect-all "requests" `
--collect-all "PIL" `
--collect-all "numpy" `
--hidden-import "tkinter" `
--hidden-import "tkinter.scrolledtext" `
--hidden-import "tkinter.messagebox" `
--hidden-import "tkinter.ttk" `
--hidden-import "requests" `
--hidden-import "PIL" `
--hidden-import "numpy" `
--hidden-import "cv2" `
--hidden-import "ppadb" `
--hidden-import "ultralytics" `
--paths "dist" `
"dist/main_farm_ruong_nguyen.py"



copy auth vào _interval
