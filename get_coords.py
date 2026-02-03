import pyautogui
import time
import sys

print("=== 鼠标坐标获取工具 ===")
print("请将鼠标移动到你要点击的按钮上，然后保持不动。")
print("按下 'Ctrl+C' 停止获取。\n")

try:
    while True:
        x, y = pyautogui.position()
        position_str = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        print(position_str, end='')
        print('\b' * len(position_str), end='', flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n已停止。请将记录下的坐标填入 flash_mcu_script.py 中。")

