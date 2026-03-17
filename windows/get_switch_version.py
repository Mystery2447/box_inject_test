import serial
import time
import sys
import re

# ================= 配置区域 =================
MCU_SERIAL_PORT = "COM23"       # 串口
MCU_BAUDRATE = 115200          # 波特率
TIMEOUT = 2.0                  # 读取超时

# 查询版本的命令
# 如果你不确定命令，可以尝试: "swtcmd version", "swt version", "version", "show version"
VERSION_CMD = "switch -v" 
# ===========================================

def get_switch_version():
    print(f"=== Switch 版本查询工具 ===")
    print(f"串口: {MCU_SERIAL_PORT} @ {MCU_BAUDRATE}")
    
    try:
        ser = serial.Serial(MCU_SERIAL_PORT, MCU_BAUDRATE, timeout=TIMEOUT)
        print("✅ 串口已打开")
        
        # 1. 先清空缓冲区
        ser.reset_input_buffer()
        
        # 2. 发送回车激活终端（可选）
        ser.write(b"\r\n")
        time.sleep(0.5)
        
        # 3. 发送查询命令
        cmd = VERSION_CMD + "\r\n"
        print(f"TX > {VERSION_CMD}")
        ser.write(cmd.encode('utf-8'))
        
        # 4. 读取响应 (修改为读取后续 5 行)
        print("\n--- 响应内容 (前5行) ---")
        
        line_count = 0
        start_time = time.time()
        
        # 读取直到超时或者读满5行
        while time.time() - start_time < TIMEOUT + 2.0:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line: # 忽略空行
                        # 忽略回显 (如果是刚发送的命令本身)
                        if VERSION_CMD in line:
                            continue
                            
                        print(f"Line {line_count+1}: {line}")
                        line_count += 1
                        
                        if line_count >= 5:
                            break
                except Exception:
                    pass
            else:
                time.sleep(0.1)
            
        print("----------------")
        ser.close()
        
        if line_count == 0:
            print("[提示] 未收到有效响应，请检查串口连接或命令是否正确。")
            
    except serial.SerialException as e:
        print(f"❌ 串口错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    # 支持命令行传参覆盖默认命令
    # 用法: python get_switch_version.py "custom command"
    if len(sys.argv) > 1:
        VERSION_CMD = sys.argv[1]
        
    get_switch_version()

