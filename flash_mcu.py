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


def main():
    parser = argparse.ArgumentParser(description='Infineon MCU 刷写自动化脚本')
    parser.add_argument('car', help='车型: P03/Thor/C01')
    parser.add_argument('uuid', help='MCU_UUID')
    args = parser.parse_args()

    car = args.car
    if car.lower() not in ('p03', 'thor', 'c01'):
        print('❌ 不支持的车型，请使用 P03/Thor/C01')
        sys.exit(1)

    # 标准化车型名称
    car_key = car.upper() if car.lower() == 'p03' else car.capitalize()

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