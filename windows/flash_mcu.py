import os
import sys
import time
import argparse
from pywinauto.timings import Timings

from common.config import CAR_CONFIG
from common.utils import (
    clean_old_firmware,
    get_download_url,
    download_file,
    automate_infineon_flash,
)

# 设置 pywinauto 超时时间
Timings.window_find_timeout = 10
Timings.app_start_timeout = 30

import sys
import os
import traceback

def flash_mcu(car_type, uuid):
    """
    Infineon MCU 刷写自动化函数
    
    Args:
        car_type (str): 车型 (ORINX/Thor/ORINY)
        uuid (str): MCU的UUID
    
    Returns:
        bool: 刷写成功返回True，失败返回False
    """
    # ===== 车型验证 =====
    if car_type.lower() not in ('oriny', 'thor', 'orinx'):
        print(f'❌ 不支持的车型: {car_type}，请使用 ORINX/THOR/ORINY')
        return False

    # 标准化车型名称
    car_key = car_type.lower() 
    # ===== 从配置获取 MCU 工具目录 =====
    try:
        config = CAR_CONFIG[car_key]
        mcu_dir = config["mcu_dir"]
    except KeyError:
        print(f"❌ 错误: 未找到车型 {car_key} 的配置信息")
        return False
    
    app_path = r"C:\Program Files\Infineon\Memtool 2021\IMTMemtool.exe"

    print("=" * 60)
    print("Infineon MCU 刷写自动化脚本")
    print("=" * 60)
    print(f"[配置] 车型: {car_key}")
    print(f"[配置] MCU 工具目录: {mcu_dir}")
    print(f"[配置] UUID: {uuid}")
    print()

    # ===== 步骤 1: 清理旧 hex 文件 =====
    print("[步骤 1] 清理旧 hex 文件...")
    try:
        clean_old_firmware(mcu_dir, file_ext=".hex")
        print("✅ 清理完成")
    except NameError:
        print("⚠️  警告: clean_old_firmware 函数未定义，跳过清理步骤")
    except Exception as e:
        print(f"⚠️  清理旧文件时出错: {e}")
    print()

    # ===== 步骤 2: 下载新固件 =====
    print("[步骤 2] 下载 MCU 固件...")

    try:
        mcu_download_url = get_download_url(uuid, car_key, artifact_type="mcus")
    except NameError:
        print("❌ 错误: get_download_url 函数未定义")
        return False

    if mcu_download_url:
        try:
            downloaded_file = download_file(mcu_download_url, mcu_dir)
            if downloaded_file:
                print(f"✅ MCU 固件下载成功: {os.path.basename(downloaded_file)}")
            else:
                print("❌ 下载失败")
                return False
        except NameError:
            print("❌ 错误: download_file 函数未定义")
            return False
        except Exception as e:
            print(f"❌ 下载过程出错: {e}")
            return False
    else:
        print("❌ 错误: 无法获取 MCU 固件下载链接")
        return False
    print()

    # ===== 步骤 3: 自动化刷写 =====
    print("[步骤 3] 启动 Infineon Memtool 并自动化刷写...")
    
    if not os.path.exists(app_path):
        print(f"❌ Infineon 应用不存在: {app_path}")
        return False

    try:
        success = automate_infineon_flash(app_path, mcu_dir)
        if success:
            print("✅ MCU 刷写完成")
            return True
        else:
            print("❌ MCU 刷写失败")
            return False
    except NameError:
        print("❌ 错误: automate_infineon_flash 函数未定义")
        return False
    except Exception as e:
        print(f"❌ 自动化刷写失败: {e}")
        traceback.print_exc()
        return False    



def main():
    parser = argparse.ArgumentParser(description='Infineon MCU 刷写自动化脚本')
    parser.add_argument('car', help='车型: P03/Thor/C01')
    parser.add_argument('uuid', help='MCU_UUID')
    args = parser.parse_args()

    car = args.car
    if car.lower() not in ('oriny', 'thor', 'orinx'):
        print('❌ 不支持的车型，请使用 ORINX/THOR/ORINY')
        sys.exit(1)

    # 标准化车型名称
    car_key = car.lower() if car.lower() == 'oriny' else car.capitalize()

    # 从配置获取 MCU 工具目录
    config = CAR_CONFIG[car_key]
    mcu_dir = config["mcu_dir"]
    app_path = r"C:\Program Files\Infineon\Memtool 2021\IMTMemtool.exe"

    print("=" * 60)
    print("Infineon MCU 刷写自动化脚本")
    print("=" * 60)
    print(f"[配置] 车型: {car_key}")
    print(f"[配置] MCU 工具目录: {mcu_dir}")
    print(f"[配置] UUID: {args.uuid}")
    print()

    # ===== 步骤 1: 清理旧 hex 文件 =====
    print("[步骤 1] 清理旧 hex 文件...")
    clean_old_firmware(mcu_dir, file_ext=".hex")
    print()

    # ===== 步骤 2: 下载新固件 =====
    print("[步骤 2] 下载 MCU 固件...")

    mcu_download_url = get_download_url(args.uuid, car_key, artifact_type="mcus")

    if mcu_download_url:
        downloaded_file = download_file(mcu_download_url, mcu_dir)
        if downloaded_file:
            print(f"✅ MCU 固件下载成功: {os.path.basename(downloaded_file)}")
        else:
            print("❌ 下载失败")
            sys.exit(1)
    else:
        print("❌ 错误: 无法获取 MCU 固件下载链接")
        sys.exit(1)
    print()

    # ===== 步骤 3: 自动化刷写 =====
    print("[步骤 3] 启动 Infineon Memtool 并自动化刷写...")
    if not os.path.exists(app_path):
        print(f"❌ Infineon 应用不存在: {app_path}")
        sys.exit(1)

    try:
        # 传递 mcu_dir 而不是 downloaded_file，让函数自动选择最长的 hex 文件
        success = automate_infineon_flash(app_path, mcu_dir)
        if success:
            print("✅ MCU 刷写完成")
            return True
        else:
            print("❌ MCU 刷写失败")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 自动化刷写失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()