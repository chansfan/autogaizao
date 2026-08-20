import time
import random
import threading
import os
import pyautogui
import pyperclip
import keyboard
import tkinter as tk
from tkinter import messagebox

# ==================== 默认配置（如果 config.txt 不存在则使用） ====================
DEFAULT_CONFIG = {
    "ALT_POS": "142,360",          # 改造石坐标
    "EQUIP_POS": "449,604",        # 装备坐标
    "KEYWORDS": "最大生命,火焰抗性,攻击速度,暴击率",  # 关键词，英文逗号分隔
    "MAX_ATTEMPTS": "1000",
    "CLICK_DELAY": "0.8",
    "HOVER_DELAY": "0.6",
    "START_HOTKEY": "F6",
    "STOP_HOTKEY": "F7",
    "EXIT_HOTKEY": "F8",
}

CONFIG_FILE = "config.txt"

# ==================== 配置文件读写 ====================
def load_config():
    """从 config.txt 读取配置，如果不存在则创建默认配置"""
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
    """将 "x,y" 字符串解析为 (x, y) 元组"""
    parts = s.split(",")
    return (int(parts[0].strip()), int(parts[1].strip()))

def parse_keywords(s):
    """将逗号分隔的关键词字符串解析为列表，忽略空项"""
    return [kw.strip() for kw in s.split(",") if kw.strip()]

# ==================== 加载配置 ====================
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

# ==================== 全局事件 ====================
pyautogui.FAILSAFE = True
start_event = threading.Event()
stop_event = threading.Event()

def safe_click(pos, button='left'):
    x, y = pos
    pyautogui.moveTo(x + random.randint(-3, 3), y + random.randint(-3, 3), duration=0.15)
    time.sleep(random.uniform(0.1, 0.3))
    pyautogui.click(button=button)
    time.sleep(CLICK_DELAY)

def use_alt():
    safe_click(ALT_POS, button='right')
    time.sleep(0.3)
    safe_click(EQUIP_POS, button='left')
    time.sleep(HOVER_DELAY)

def get_item_text():
    pyautogui.moveTo(EQUIP_POS[0], EQUIP_POS[1], duration=0.2)
    time.sleep(0.3)
    pyperclip.copy('')
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
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

def show_message(title, msg):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, msg)
    root.destroy()

def craft_loop():
    while True:
        start_event.wait()
        start_event.clear()
        stop_event.clear()
        attempts = 0
        write_log(f"开始运行，关键词：{KEYWORDS}")
        while attempts < MAX_ATTEMPTS and not stop_event.is_set():
            use_alt()
            text = get_item_text()
            found, kw = check_keywords(text)
            write_log(f"第 {attempts+1} 次尝试，物品信息：\n{text}\n")
            if found:
                write_log(f"✅ 命中关键词：{kw}，停止！")
                show_message("洗词条工具", f"已找到目标词条：{kw}")
                break
            attempts += 1
            time.sleep(random.uniform(0.5, 1.0))
        if not stop_event.is_set() and attempts >= MAX_ATTEMPTS:
            write_log("❌ 达到最大尝试次数，未找到目标词条")
            show_message("洗词条工具", "未找到目标词条")
        print("任务结束，按 F6 可重新开始")

def start_craft():
    if not start_event.is_set():
        print("收到开始指令")
        start_event.set()

def stop_craft():
    print("收到停止指令")
    stop_event.set()

def exit_program():
    print("退出程序")
    stop_event.set()
    start_event.set()
    os._exit(0)

def main():
    keyboard.add_hotkey(START_HOTKEY, start_craft)
    keyboard.add_hotkey(STOP_HOTKEY, stop_craft)
    keyboard.add_hotkey(EXIT_HOTKEY, exit_program)
    print(f"洗词条工具已启动，关键词：{KEYWORDS}")
    print(f"按 {START_HOTKEY} 开始，按 {STOP_HOTKEY} 停止，按 {EXIT_HOTKEY} 退出")
    t = threading.Thread(target=craft_loop, daemon=True)
    t.start()
    keyboard.wait()

if __name__ == '__main__':
    main()