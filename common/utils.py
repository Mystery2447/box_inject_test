import os
import sys
import glob
import time
import zipfile
import requests
import serial
from .config import API_BASE_URL, API_TOKEN, MCU_SERIAL_PORT, MCU_BAUDRATE, SERIAL_TIMEOUT

def clean_old_firmware(directory, file_ext=".bin"):
    """
    清理目录下的固件文件
    
    清理规则：
    - SWITCH (.bin 文件): 删除所有 bin 文件
    - MCU (.hex 文件): 删除所有 hex 文件，但保留文件名中包含 "HSM" 或 "AB" 的文件
    
    Args:
        directory: 目录路径
        file_ext: 文件扩展名，如 ".bin" 或 ".hex"
    """
    if not os.path.exists(directory):
        print(f"❌ 严重错误: 找不到工具目录: {directory}")
        print("请检查路径配置 CAR_CONFIG 是否正确，或文件夹是否存在。")
        sys.exit(1)
    
    # 确保扩展名以 . 开头
    if not file_ext.startswith("."):
        file_ext = "." + file_ext
    
    print(f"[清理] 正在清理固件文件 ({file_ext}): {directory}")
    
    pattern = os.path.join(directory, f"*{file_ext}")
    files = glob.glob(pattern)
    
    if not files:
        print(f"  目录中没有 {file_ext} 文件，无需清理")
        return
    
    deleted_count = 0
    for f in files:
        filename = os.path.basename(f)
        filename_upper = filename.upper()  # 转换为大写，用于不区分大小写的匹配
        
        # MCU (.hex 文件): 保留文件名中包含 "HSM" 或 "AB" 的文件
        if file_ext == ".hex":
            if "HSM" in filename_upper or "AB" in filename_upper:
                print(f"  保留文件（包含 HSM 或 AB）: {filename}")
                continue
        
        # 删除文件
        try:
            os.remove(f)
            print(f"  - 已删除: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"  - 删除失败 {filename}: {e}")
    
    if deleted_count == 0:
        print(f"  没有需要清理的文件")
    else:
        print(f"  共清理 {deleted_count} 个文件")

def get_download_url(input_id, car_model, artifact_type="switches"):
    """
    获取下载链接: input_id 就是制品库的UUID
    artifact_type: switches / mcus / socs (根据 API 路径调整)
    """
    print(f"\n[API] 正在处理 ID: {input_id} (车型: {car_model}, 类型: {artifact_type})")
    
    headers = {
        'Authorization': API_TOKEN,
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    print(f"[API] 正在查询 {artifact_type} Artifact UUID...")
    
    # 动态构建 API 路径
    # SOC 使用 /api/v1/artifacts/ 路径，SWITCH 和 MCU 使用 /api/v1/packages/ 路径
    if artifact_type == "socs":
        url = f"{API_BASE_URL}/api/v1/artifacts/{artifact_type}/{input_id}"
    else:
        url = f"{API_BASE_URL}/api/v1/packages/{artifact_type}/{input_id}"
    
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        r.raise_for_status()
        
        print("[API] 获取详情成功")
        data = r.json()
        
        dl_url = None
        if 'data' in data and isinstance(data['data'], dict):
             dl_url = data['data'].get('url') or data['data'].get('downloadUrl')
        
        if not dl_url:
            dl_url = data.get("url") or data.get("downloadUrl")
            
        if dl_url:
            print(f"[API] 成功解析下载链接: {dl_url}")
            return dl_url
        else:
            print(f"❌ API 响应中未找到 url 字段: {data}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"[API Error] HTTP 错误: {e}")
        if hasattr(e.response, 'text'):
            print(f"   响应内容: {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"[API Error] 查询失败: {e}")
        return None

def download_file(url, save_dir):
    """通用文件下载函数（带进度显示）"""
    if not url:
        return None
        
    filename = url.split('/')[-1].split('?')[0]
    save_path = os.path.join(save_dir, filename)
    
    print(f"[下载] 开始下载: {filename}")
    try:
        with requests.get(url, stream=True, verify=False) as r:
            r.raise_for_status()
            
            # 获取文件总大小（字节）
            total_size = int(r.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 计算并显示进度
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            # 格式化文件大小显示
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            # 使用 \r 在同一行更新进度
                            print(f"\r[下载进度] {percent:.1f}% ({downloaded_mb:.2f} MB / {total_mb:.2f} MB)", end='', flush=True)
                        else:
                            # 如果无法获取总大小，只显示已下载量
                            downloaded_mb = downloaded / (1024 * 1024)
                            print(f"\r[下载进度] 已下载: {downloaded_mb:.2f} MB", end='', flush=True)
            
            # 下载完成后换行
            print()  # 换行，避免进度信息被覆盖
            print(f"[下载] 完成: {save_path}")
            return save_path
    except Exception as e:
        print(f"\n[下载失败] {e}")
        return None

def find_firmware_file_bin(directory):
    """在指定目录下查找最新的 bin 文件"""
    if not os.path.exists(directory):
        print(f"❌ [错误] 目录不存在: {directory}")
        return None
        
    files = glob.glob(os.path.join(directory, "*.bin"))
    
    # 如果目录里根本没有 .bin 文件
    if not files:
        print(f"❌ [错误] 目录中未找到任何 .bin 文件: {directory}")
        return None
    
    # 返回创建时间最新的 .bin 文件
    return max(files, key=os.path.getctime)

def find_firmware_file_hex(directory):
    """在指定目录下查找最新的 hex 文件（用于 MCU 刷写）"""
    if not os.path.exists(directory):
        print(f"❌ [错误] 目录不存在: {directory}")
        return None
        
    files = glob.glob(os.path.join(directory, "*.hex"))
    
    # 如果目录里根本没有 .hex 文件
    if not files:
        print(f"❌ [错误] 目录中未找到任何 .hex 文件: {directory}")
        return None
    
    # 返回创建时间最新的 .hex 文件
    return max(files, key=os.path.getctime)

def extract_zip_file(zip_path, extract_to=None):
    """
    解压 ZIP 文件到指定目录
    zip_path: ZIP 文件路径
    extract_to: 解压目标目录，如果为 None 则解压到 ZIP 文件所在目录
    """
    if not os.path.exists(zip_path):
        print(f"❌ [错误] ZIP 文件不存在: {zip_path}")
        return False
    
    # 如果没有指定解压目录，则解压到 ZIP 文件所在目录
    if extract_to is None:
        extract_to = os.path.dirname(zip_path)
    
    print(f"[解压] 开始解压: {os.path.basename(zip_path)}")
    print(f"[解压] 目标目录: {extract_to}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取 ZIP 文件中的所有文件列表
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            
            # 解压所有文件
            zip_ref.extractall(extract_to)
            
            print(f"[解压] 完成: 已解压 {total_files} 个文件")
            return True
    except zipfile.BadZipFile:
        print(f"❌ [错误] 无效的 ZIP 文件: {zip_path}")
        return False
    except Exception as e:
        print(f"❌ [解压失败] {e}")
        return False

def check_mcu_connection():
    """检查 MCU 串口连接并发送心跳"""
    try:
        ser = serial.Serial(MCU_SERIAL_PORT, MCU_BAUDRATE, timeout=SERIAL_TIMEOUT)
        if ser.is_open:
            print(f"\n[串口] 连接 MCU ({MCU_SERIAL_PORT}) 成功")
            
            max_retries = 3
            handshake_success = False
            
            for i in range(max_retries):
                print(f"[串口] 尝试发送心跳 ({i+1}/{max_retries})...")
                ser.reset_input_buffer()
                
                cmd = "swtcmd hb 0\r\n"
                ser.write(cmd.encode('utf-8'))
                time.sleep(0.5)
                start_read = time.time()
                while time.time() - start_read < 2.0:
                    if ser.in_waiting:
                        try:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if "swtcmd hb 0" in line:
                                print(f"✅ 收到确认: {line}")
                                handshake_success = True
                                break
                        except:
                            pass
                    else:
                        time.sleep(0.1)
                
                if handshake_success:
                    break
                else:
                    print("⚠️ 未收到预期回显")
            
            if not handshake_success:
                print("❌ 警告: 3次心跳尝试均未收到有效回显，MCU 可能未响应！")
            
            ser.close()
            return handshake_success
    except Exception as e:
        print(f"[串口] 连接失败: {e} (将尝试继续)")
        return False

