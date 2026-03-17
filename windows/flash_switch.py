import os
import sys
import subprocess
from common.config import CAR_CONFIG
from common.utils import clean_old_firmware, get_download_url, download_file, find_firmware_file_bin, check_mcu_connection


def flash_switch(cartype, uuid):
    """
    SWITCH 线刷自动化函数
    
    Args:
        cartype (str): 车型 (P03/Thor/C01)
        uuid (str): 设备的UUID
    
    Returns:
        bool: 刷写成功返回True，失败返回False
    """
    print("=== SWITCH 线刷自动化脚本 \n")
    
    # ===== 1. 参数验证和车型标准化 =====
    if not cartype or not uuid:
        print("❌ 错误: 必须提供车型和UUID参数")
        return False
    
    cartype = cartype.strip()
    uuid = uuid.strip()
    
    # 确定车型
    if cartype.lower() == "oriny":
        car_model = "oriny"
    elif cartype.lower() == "thor":
        car_model = "thor"
    elif cartype.lower() == "orinx":
        car_model = "orinx"
    else:
        print(f"❌ 错误: 不支持的车型 '{cartype}'")
        print("支持的车型列表: oriny, thor, orinx")
        return False

    print(f"[配置] 目标 UUID: {uuid}")
    
    # ===== 2. 获取配置 =====
    try:
        config = CAR_CONFIG[car_model]
        target_switch_dir = config["switch_dir"]
    except KeyError:
        print(f"❌ 错误: 未找到车型 {car_model} 的配置信息")
        return False
    except Exception as e:
        print(f"❌ 配置获取失败: {e}")
        return False
    
    print(f"\n已选择车型: {car_model}")
    print(f"工具路径: {target_switch_dir}")
    
    # ===== 3. MCU 串口唤醒 =====
    try:
        check_mcu_connection()
    except NameError:
        print("⚠️  警告: check_mcu_connection 函数未定义，跳过唤醒步骤")
    except Exception as e:
        print(f"⚠️  MCU唤醒过程出错: {e}")
        # 根据实际情况决定是否继续
        # return False

    # ===== 4. 固件准备 =====
    # A. 清理旧文件
    try:
        clean_old_firmware(target_switch_dir)
    except NameError:
        print("⚠️  警告: clean_old_firmware 函数未定义，跳过清理步骤")
    except Exception as e:
        print(f"⚠️  清理旧文件时出错: {e}")
    
    # B. 获取下载链接
    try:
        switch_download_url = get_download_url(uuid, car_model, artifact_type="switches")
    except NameError:
        print("❌ 错误: get_download_url 函数未定义")
        return False
    except Exception as e:
        print(f"❌ 获取下载链接失败: {e}")
        return False
    
    # C. 执行下载
    if switch_download_url:
        try:
            download_file(switch_download_url, target_switch_dir)
        except NameError:
            print("❌ 错误: download_file 函数未定义")
            return False
        except Exception as e:
            print(f"❌ 下载固件失败: {e}")
            return False
    else:
        print("❌ 错误: 无法获取固件下载链接，流程终止。")
        return False

    # ===== 5. 查找最终要刷的文件 =====
    try:
        fw_file = find_firmware_file_bin(target_switch_dir)
        if not fw_file:
            print("[错误] 目录为空，无法进行刷写！")
            return False
        print(f"找到固件文件: {fw_file}")
    except NameError:
        print("❌ 错误: find_firmware_file_bin 函数未定义")
        return False
    except Exception as e:
        print(f"❌ 查找固件文件失败: {e}")
        return False

    # ===== 6. 执行刷写 =====
    try:
        if flash_process_wrapper(target_switch_dir, fw_file, f"{car_model} Switch"):
            print(f"✅ {car_model} Switch 刷写成功")
            # 注意: 刷写后不清理文件，保留在目录中
            return True
        else:
            print(f"❌ {car_model} Switch 刷写失败")
            return False
    except NameError:
        print("❌ 错误: flash_process_wrapper 函数未定义")
        return False
    except Exception as e:
        print(f"❌ 刷写过程出错: {e}")
        return False

def flash_process_wrapper(directory, firmware_file, desc="Switch"):
    """封装单次刷写流程 (Switch 专用)"""
    bin_filename = os.path.basename(firmware_file)
    print(f"\n>>> 准备刷写 {desc}")
    print(f"    目录: {directory}")
    print(f"    文件: {bin_filename}")
    
    # 切换目录
    os.chdir(directory)
    
    # 执行批处理
    cmd = f"fwupdate_vector_fw.bat {bin_filename}"
    print(f"[CMD] 执行: {cmd}")
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        shell=True,
        text=True
    )
    
    success_flag = False
    print("---------------- 刷写日志 ----------------")
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            line = output.strip()
            print(line)
            # 5. 检测结束标志
            if "marvell jtag spi flash programmer finished successfully" in line.lower():
                success_flag = True
    print("----------------------------------------")
    return success_flag

def main():
    print("=== SWITCH 线刷自动化脚本 \n")
    
    # 1. 解析命令行参数
    if len(sys.argv) < 3:
        print("❌ 错误: 参数不足")
        print("用法: python flash_switch.py <车型> <UUID>")
        print("示例: python flash_switch.py Thor 3efe73e3-...")
        sys.exit(1)
        
    car_input = sys.argv[1].strip()
    input_uuid = sys.argv[2].strip()
    
    # 确定车型
    if car_input.lower() == "oriny":
        car_model = "oriny"
    elif car_input.lower() == "thor":
        car_model = "thor"
    elif car_input.lower() == "orinx":
        car_model = "orinx"
    else:
        print(f"❌ 错误: 不支持的车型 '{car_input}'")
        print("支持的车型列表: oriny, thor, orinx")
        sys.exit(1)

    print(f"[配置] 目标 UUID: {input_uuid}")
    
    config = CAR_CONFIG[car_model]
    target_switch_dir = config["switch_dir"]
    
    print(f"\n已选择车型: {car_model}")
    print(f"工具路径: {target_switch_dir}")
    
    # 2. MCU 串口唤醒 (使用通用工具)
    check_mcu_connection()

    # 3. 固件准备 (清理 -> 下载)
    # A. 清理旧文件
    clean_old_firmware(target_switch_dir)
    
    # B. 获取下载链接
    Switch_download_url = get_download_url(input_uuid, car_model, artifact_type="switches")
    
    # C. 执行下载
    if Switch_download_url:
        download_file(Switch_download_url, target_switch_dir)
    else:
        print("❌ 错误: 无法获取固件下载链接，流程终止。")
        return

    # 4. 查找最终要刷的文件（只要 .bin 文件即可）
    fw_file = find_firmware_file_bin(target_switch_dir)
    if not fw_file:
        print("[错误] 目录为空，无法进行刷写！")
        return

    # 5. 执行刷写
    if flash_process_wrapper(target_switch_dir, fw_file, f"{car_model} Switch"):
        print(f"✅ {car_model} Switch 刷写成功")
        # 注意: 刷写后不清理文件，保留在目录中
        return True
    else:
        print(f"❌ {car_model} Switch 刷写失败")
        return False

if __name__ == "__main__":
    main()

