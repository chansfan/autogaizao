import time
import random
import threading
import os
import pyautogui
import pyperclip
import keyboard
import tkinter as tk
from tkinter import messagebox

import pystray
from PIL import Image, ImageDraw

# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    "ALT_POS": "142,360",
    "EQUIP_POS": "449,604",
    "KEYWORDS": "最大生命,火焰抗性,攻击速度,暴击率",
    "MAX_ATTEMPTS": "1000",
    "CLICK_DELAY": "0.05",
    "HOVER_DELAY": "0.1",          # 悬停等待已缩短
    "START_HOTKEY": "F6",
    "STOP_HOTKEY": "F7",
    "EXIT_HOTKEY": "F8",
}

CONFIG_FILE = "config.txt"

def load_config():
    config = DEFAULT_CONFIG.copy()
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("# 洗词条工具配置文件\n")
            f.write("# 每行一个配置项，格式：键=值\n")
            f.write("# 关键词用英文逗号分隔，例如：最大生命,火焰抗性\n")
            f.write("# 修改后保存，重新启动程序生效\n\n")
            for key, value in DEFAULT_CONFIG.items():
                f.write(f"{key}={value}\n")
        return config
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in config:
                        config[key] = value
        return config

def parse_coord(s):
    parts = s.split(",")
    return (int(parts[0].strip()), int(parts[1].strip()))

def parse_keywords(s):
    return [kw.strip() for kw in s.split(",") if kw.strip()]

cfg = load_config()
ALT_POS = parse_coord(cfg["ALT_POS"])
EQUIP_POS = parse_coord(cfg["EQUIP_POS"])
KEYWORDS = parse_keywords(cfg["KEYWORDS"])
MAX_ATTEMPTS = int(cfg["MAX_ATTEMPTS"])
CLICK_DELAY = float(cfg["CLICK_DELAY"])
HOVER_DELAY = float(cfg["HOVER_DELAY"])
START_HOTKEY = cfg["START_HOTKEY"]
STOP_HOTKEY = cfg["STOP_HOTKEY"]
EXIT_HOTKEY = cfg["EXIT_HOTKEY"]

pyautogui.FAILSAFE = True
start_event = threading.Event()
stop_event = threading.Event()
exit_event = threading.Event()

root = None
status_label = None
keyword_entry = None

def safe_click(pos, button='left'):
    x, y = pos
    pyautogui.moveTo(x + random.randint(-2, 2), y + random.randint(-2, 2), duration=0.03)
    time.sleep(random.uniform(0.02, 0.05))
    pyautogui.click(button=button)
    time.sleep(CLICK_DELAY)

def use_alt():
    safe_click(ALT_POS, button='right')
    time.sleep(0.1)               # 右键到左键间隔固定 0.1
    safe_click(EQUIP_POS, button='left')
    time.sleep(0.1)               # 悬停等待缩短为 0.1 秒（原来用 HOVER_DELAY，现在直接固定）

def get_item_text():
    pyautogui.moveTo(EQUIP_POS[0], EQUIP_POS[1], duration=0.03)
    time.sleep(0.02)              # 悬停稳定时间缩短
    pyperclip.copy('')
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.05)              # 复制等待缩短
    return pyperclip.paste()

def check_keywords(text):
    clean_text = ''.join(text.split())
    for kw in KEYWORDS:
        clean_kw = ''.join(kw.split())
        if clean_kw in clean_text:
            return True, kw
    return False, None

def write_log(msg):
    with open('craft_log.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def craft_loop():
    while not exit_event.is_set():
        start_event.wait()
        start_event.clear()
        stop_event.clear()
        attempts = 0
        write_log(f"开始运行，关键词：{KEYWORDS}")
        while attempts < MAX_ATTEMPTS and not stop_event.is_set() and not exit_event.is_set():
            use_alt()
            text = get_item_text()
            found, kw = check_keywords(text)
            write_log(f"第 {attempts+1} 次尝试，物品信息：\n{text}\n")
            if found:
                write_log(f"✅ 命中关键词：{kw}，停止！")
                root.after(0, lambda: messagebox.showinfo("洗词条工具", f"已找到目标词条：{kw}"))
                break
            attempts += 1
            time.sleep(random.uniform(0.05, 0.1))
        if not stop_event.is_set() and not exit_event.is_set() and attempts >= MAX_ATTEMPTS:
            write_log("❌ 达到最大尝试次数，未找到目标词条")
            root.after(0, lambda: messagebox.showinfo("洗词条工具", "未找到目标词条"))
        root.after(0, update_status, "就绪")

def update_status(text):
    if status_label:
        status_label.config(text=text)

def start_craft_from_ui():
    global KEYWORDS
    keywords_str = keyword_entry.get().strip()
    if not keywords_str:
        messagebox.showwarning("提示", "请输入关键词")
        return
    KEYWORDS = parse_keywords(keywords_str)
    update_status("运行中...")
    print("开始，关键词：", KEYWORDS)
    start_event.set()

def start_craft_hotkey():
    if not start_event.is_set():
        update_status("运行中...")
        print("热键开始，关键词：", KEYWORDS)
        start_event.set()

def stop_craft():
    print("收到停止指令")
    stop_event.set()

def exit_program():
    print("退出程序")
    exit_event.set()
    stop_event.set()
    start_event.set()
    if root:
        root.quit()
        root.destroy()
    os._exit(0)

# ==================== 托盘图标 ====================
def create_image():
    img = Image.new('RGB', (64, 64), color=(60, 60, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(200, 150, 50))
    d.text((28, 28), "C", fill=(0, 0, 0))
    return img

def show_window():
    if root:
        root.deiconify()

def hide_window():
    if root:
        root.withdraw()

def setup_tray():
    menu = pystray.Menu(
        pystray.MenuItem("显示窗口", show_window),
        pystray.MenuItem("开始 (F6)", start_craft_hotkey),
        pystray.MenuItem("停止 (F7)", stop_craft),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", exit_program)
    )
    icon = pystray.Icon("craft_tool", create_image(), "洗词条工具", menu)
    return icon

def main():
    global root, status_label, keyword_entry

    root = tk.Tk()
    root.title("洗词条工具")
    root.geometry("350x180")
    root.resizable(False, False)

    tk.Label(root, text="目标词条（用英文逗号分隔）:").pack(pady=(15,5))
    keyword_entry = tk.Entry(root, width=40)
    keyword_entry.insert(0, cfg["KEYWORDS"])
    keyword_entry.pack(pady=(0,10))

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="开始 (F6)", width=10, command=start_craft_from_ui).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="停止 (F7)", width=10, command=stop_craft).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="退出 (F8)", width=10, command=exit_program).grid(row=0, column=2, padx=5)

    status_label = tk.Label(root, text="就绪", fg="blue")
    status_label.pack(pady=(10,0))

    root.protocol('WM_DELETE_WINDOW', hide_window)

    keyboard.add_hotkey(START_HOTKEY, start_craft_hotkey)
    keyboard.add_hotkey(STOP_HOTKEY, stop_craft)
    keyboard.add_hotkey(EXIT_HOTKEY, exit_program)

    print(f"洗词条工具已启动，关键词：{KEYWORDS}")
    print(f"按 {START_HOTKEY} 开始，按 {STOP_HOTKEY} 停止，按 {EXIT_HOTKEY} 退出")

    t = threading.Thread(target=craft_loop, daemon=True)
    t.start()

    tray_icon = setup_tray()
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    root.mainloop()

if __name__ == '__main__':
    main()
