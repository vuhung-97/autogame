import sys
from auth import run_authentication
from gui_leo_am import MainApp
import tkinter as tk

if __name__ == "__main__":
    if run_authentication():
        root = tk.Tk()
        app = MainApp(root)
        root.mainloop()
    else:
        sys.exit()