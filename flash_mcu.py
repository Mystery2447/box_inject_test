import os
import sys
import time
import argparse
import glob
from pywinauto import Application
from pywinauto.timings import Timings

from common.config import CAR_CONFIG
from common.utils import (
    clean_old_firmware, 
    get_download_url, 
    download_file
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


def automate_infineon_flash(app_path, mcu_dir):
    """
    使用 pywinauto 自动化 Infineon Memtool 刷写流程
    
    Args:
        app_path: Infineon Memtool 应用路径
        mcu_dir: MCU 工具目录（会自动选择名字最长的 hex 文件）
    
    Returns:
        bool: 刷写是否成功
    """
    try:
        # 1. 启动应用并获取主窗口
        app, main_window = launch_application(app_path)
        if not app or not main_window:
            return False
        
        # 3. 连接设备
        print("开始连接设备...")
        if not connect_device(app, main_window):
            print("❌ 连接设备失败")
            return False
        
        # 5. 导入刷写文件 (HSM)
        print("开始导入刷写文件 (HSM)...")
        # 查找 HSM 文件
        import glob
        all_hex_files = glob.glob(os.path.join(mcu_dir, "*.hex"))
        hsm_file = None
        for f in all_hex_files:
            if "disable" in os.path.basename(f).lower() and "HSM" in os.path.basename(f):
                hsm_file = f
                break
        
        if not hsm_file:
            print("❌ 未找到 HSM 文件 (包含 disable 和 HSM)")
            return False
            
        if not import_hex_file(app, main_window, hsm_file):
            print("❌ 导入 HSM 文件失败")
            return False
        
        print("✅ HSM 文件导入成功")
        time.sleep(2)  # 等待文件加载完成
        
        # 6. 执行刷写操作 (HSM)
        print("开始执行刷写操作 (HSM)...")
        if not execute_flash_program_1(app, main_window):
            print("❌ HSM 刷写操作失败")
            return False
        
        print("✅ HSM 刷写操作完成")
        
        # 7. 断开连接再重新连接
        print("断开设备连接...")
        if not disconnect_device(main_window):
            print("⚠️ 断开连接失败，尝试继续连接...")
        
        time.sleep(1)
        print("重新连接设备...")
        if not connect_device(app, main_window):
            print("❌ 重新连接设备失败")
            return False    
        
        # 9. 执行刷写操作 (HSM 擦除)
        print("开始执行刷写操作 (HSM 擦除)...")
        if not execute_flash_program_2(app, main_window):
            print("❌ HSM 擦除操作失败")
            return False
        
        
        # 10. 导入 AB 文件
        print("开始导入 AB 文件...")
        ab_file = None
        for f in all_hex_files:
            if "AB" in os.path.basename(f):
                ab_file = f
                break
        
        if not ab_file:
            print("❌ 未找到 AB 文件")
            return False
            
        if not import_hex_file(app, main_window, ab_file):
            print("❌ 导入 AB 文件失败")
            return False
            
        print("✅ AB 文件导入成功")
        time.sleep(2)
        
        # 11. 执行刷写操作 (AB)
        print("开始执行刷写操作 (AB)...")
        if not execute_flash_program_3(app, main_window):
            print("❌ AB 刷写操作失败")
            return False
            
        
        # 12. 导入 MCU 文件 (下载的文件)
        print("开始导入 MCU 文件...")
        mcu_file = None
        if all_hex_files:
            # 排除 HSM 和 AB 文件，然后找最长的
            candidates = []
            for f in all_hex_files:
                if f != hsm_file and f != ab_file:
                    candidates.append(f)
            
            if candidates:
                mcu_file = max(candidates, key=lambda f: len(os.path.basename(f)))
                print(f"✅ 找到下载的 MCU 文件: {os.path.basename(mcu_file)}")
            else:
                print("⚠️ 未找到额外的 MCU 文件")
        
        if not mcu_file:
            print("❌ 未找到 MCU 文件")
            return False
            
        if not import_hex_file(app, main_window, mcu_file):
            print("❌ 导入 MCU 文件失败")
            return False
            
        print("✅ MCU 文件导入成功")
        time.sleep(2)
        
        # 13. 执行刷写操作 (MCU)
        print("开始执行刷写操作 (MCU)...")
        if not execute_flash_program_4(app, main_window):
            print("❌ MCU 刷写操作失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def launch_application(app_path):
    """
    启动 Infineon Memtool 应用并等待窗口出现
    
    Args:
        app_path: Infineon Memtool 应用路径
    
    Returns:
        tuple: (app, main_window) 如果成功，否则返回 (None, None)
    """
    try:
        # 1. 启动应用
        print("启动 Infineon Memtool...")
        app = Application(backend="win32").start(app_path)
        
        print("查找主窗口...")
        main_window = None  # 初始化为 None，后面会被赋值为 pywinauto 窗口对象
        max_window_retries = 20  # 最多等待10秒（20次 * 0.5秒）
        
        for i in range(max_window_retries):
            try:
                # 尝试获取顶层窗口
                main_window = app.top_window()
                
                # 检查窗口是否真的存在且可见
                if main_window.exists() and main_window.is_visible():
                    print(f"✅ 找到主窗口: {main_window.window_text()}")
                    break
            except Exception as e:
                if i == 0:
                    print(f"  等待窗口出现... ({e})")
                pass
            time.sleep(0.5)
        
        # 如果窗口还没出现，报错
        if not main_window or not main_window.exists():
            print("❌ 错误: 应用窗口未出现或无法访问")
            print("   可能原因:")
            print("   1. 应用启动失败")
            print("   2. 窗口被其他程序遮挡")
            print("   3. 应用需要更长时间启动")
            return None, None
        
        # 最终检查窗口状态
        if not main_window.exists():
            print("❌ 错误: 窗口不存在")
            return None, None
        
        # 2. 确保窗口可见并激活
        if not main_window.is_visible():
            main_window.show()
        
        main_window.set_focus()
        time.sleep(1)
        
        return app, main_window
        
    except Exception as e:
        print(f"❌ 启动应用时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def connect_device(app, main_window):
    """
    连接设备（查找并点击 Connect 按钮，验证连接成功）
    
    Args:
        app: pywinauto Application 对象 (用于查找弹窗)
        main_window: 主窗口对象
    
    Returns:
        bool: 连接是否成功
    """
    try:
        # 1. 查找并点击 Connect 按钮
        print("查找 Connect 按钮...")
        
        # 等待按钮出现（最多等待5秒）
        max_retries = 10
        connect_button = None
        for i in range(max_retries):
            try:
                connect_button = main_window.child_window(class_name="Button", title="Connect")
                if connect_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not connect_button or not connect_button.exists():
            print("❌ 无法找到 Connect 按钮")
            return False
        
        # 点击 Connect 按钮
        print("点击 Connect 按钮...")
        connect_button.click()
        
        # 2. 验证连接是否成功（查找 Disconnect 按钮）
        print("验证连接状态...")
        time.sleep(1)  # 等待连接开始
        
        # 等待 Disconnect 按钮出现（最多等待10秒）
        max_retries = 20
        disconnect_button = None
        for i in range(max_retries):
            try:
                disconnect_button = main_window.child_window(class_name="Button", title="Disconnect")
                if disconnect_button.exists():
                    print("✅ 连接成功（已找到 Disconnect 按钮）")
                    break
            except:
                pass
            time.sleep(0.5)
        
        # 如果找不到 Disconnect 按钮，说明连接失败
        if not disconnect_button or not disconnect_button.exists():
            print("❌ 连接失败（未找到 Disconnect 按钮）")
            return False
        
        # 检查是否有 "Infineon Memtool" 弹窗（可能是错误或警告），点击 OK
        # 增加重试机制，确保弹窗被捕获
        print("检查是否有弹窗...")
        max_popup_checks = 5
        popup_handled = False
        
        for i in range(max_popup_checks):
            try:
                # 1. 尝试通过标题查找 "Infineon Memtool" 的弹窗
                popup = app.window(title="Infineon Memtool")
                
                # 如果找不到，尝试查找顶层活动窗口，看是否是弹窗
                if not popup.exists():
                    active_window = app.active_window()
                    if active_window != main_window and "Infineon Memtool" in active_window.window_text():
                        popup = active_window
                
                if popup.exists() and popup.is_visible() and popup != main_window:
                    print(f"⚠️ 检测到弹窗: {popup.window_text()}")
                    
                    # 查找并点击 OK 按钮
                    ok_button = None
                    try:
                        ok_button = popup.child_window(class_name="Button", title="OK")
                        if not ok_button.exists():
                            ok_button = popup.child_window(class_name="Button", title="确定")
                    except:
                        pass
                        
                    if ok_button and ok_button.exists():
                        print("点击 OK 按钮...")
                        ok_button.click()
                        time.sleep(0.5)
                        popup_handled = True
                        break
                    else:
                        # 如果找不到 OK 按钮，尝试直接发送回车键
                        print("未找到 OK 按钮，尝试发送 Enter 键...")
                        popup.type_keys("{ENTER}")
                        time.sleep(0.5)
                        popup_handled = True
                        break
            except:
                pass
            
            time.sleep(0.5)
            
        if popup_handled:
            print("✅ 弹窗已处理")
        else:
            print("未检测到弹窗或弹窗无需处理")
            
        return True
        
    except Exception as e:
        print(f"❌ 连接设备时出错: {e}")
        return False

def disconnect_device(main_window):
    """
    断开设备（查找并点击 Disconnect 按钮，验证断开成功）
    
    Args:
        main_window: 主窗口对象
    
    Returns:
        bool: 连接是否成功
    """
    try:
        # 1. 查找并点击 Disconnect 按钮
        print("查找 Disconnect 按钮...")
        
        # 等待按钮出现（最多等待5秒）
        max_retries = 10
        dis_connect_button = None
        for i in range(max_retries):
            try:
                dis_connect_button = main_window.child_window(class_name="Button", title="Disconnect")
                if dis_connect_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not dis_connect_button or not dis_connect_button.exists():
            print("❌ 无法找到 Disconnect 按钮")
            return False
        
        # 点击 Disconnect 按钮
        print("点击 Disconnect 按钮...")
        dis_connect_button.click()
        
        # 2. 验证连接是否成功（查找 Disconnect 按钮）
        print("验证断开状态...")
        time.sleep(1)  # 等待断开开始
        
        # 等待 Connect 按钮出现（最多等待10秒）
        max_retries = 20
        connect_button = None
        for i in range(max_retries):
            try:
                connect_button = main_window.child_window(class_name="Button", title="Connect")
                if connect_button.exists():
                    print("✅ 断开成功（已找到 Connect 按钮）")
                    break
            except:
                pass
            time.sleep(0.5)
        
        # 如果找不到 Connect 按钮，说明断开失败
        if not connect_button or not connect_button.exists():
            print("❌ 断开失败（未找到 Connect 按钮）")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 断开设备时出错: {e}")
        return False


def import_hex_file(app, main_window, file_path):
    """
    导入 HEX 文件到 Infineon Memtool（通过文件路径输入）
    
    流程：
    1. 点击 Open File 按钮
    2. 匹配 "Open Hex File" 窗口
    3. 在文件路径输入框中输入完整文件路径
    4. 点击打开按钮或按 Enter
    
    Args:
        app: pywinauto Application 对象
        main_window: 主窗口对象
        file_path: HEX 文件的完整路径
    
    Returns:
        bool: 导入是否成功
    """
    try:
        # 1. 查找 "Open File" 按钮（忽略大小写）
        print("查找 Open File 按钮...")
        open_file_button = None
        max_retries = 10
        
        # 尝试多种可能的按钮标题（忽略大小写）
        button_titles = ["Open File", "Open File ..."]
        
        for i in range(max_retries):
            for title in button_titles:
                try:
                    # 尝试通过标题查找（不区分大小写）
                    open_file_button = main_window.child_window(class_name="Button", title=title)
                    if open_file_button.exists():
                        print(f"✅ 找到 Open File 按钮: {title}")
                        break
                except:
                    pass
            
            if open_file_button and open_file_button.exists():
                break
            time.sleep(0.5)
        
        if not open_file_button or not open_file_button.exists():
            print("❌ 无法找到 Open File 按钮")
            return False
        
        # 2. 点击 Open File 按钮
        print("点击 Open File 按钮...")
        open_file_button.click()
        time.sleep(1)  # 等待文件对话框出现
        
        # 3. 等待并匹配 "Open Hex File" 窗口
        print("等待文件对话框出现...")
        file_dialog = None
        max_retries = 10
        
        # 匹配 "Open Hex File" 窗口
        dialog_titles = ["Open Hex File","文件名","打开"]
        
        for i in range(max_retries):
            for title in dialog_titles:
                try:
                    file_dialog = app.window(title=title, found_index=0)
                    if file_dialog.exists():
                        print(f"✅ 找到文件对话框: {title}")
                        break
                except:
                    pass
            
            if file_dialog and file_dialog.exists():
                break
            time.sleep(0.5)
        
        if not file_dialog or not file_dialog.exists():
            print("❌ 无法找到文件对话框")
            return False
        
        time.sleep(1)  # 等待对话框完全加载
        
        # 4. 使用传入的文件路径
        target_file_path = file_path
        if not os.path.exists(target_file_path):
            print(f"❌ 文件不存在: {target_file_path}")
            return False
        print(f"目标文件路径: {target_file_path}")
        
        # 5. 在文件路径输入框中输入完整文件路径
        print(f"在文件路径输入框中输入路径...")
        
        # 尝试多种方式找到文件路径输入框（搜索框）
        path_input = None
        max_retries = 5
        
        for i in range(max_retries):
            try:
                # 方法1: 查找文件名输入框（通常在对话框底部，Edit 控件）
                path_input = file_dialog.child_window(class_name="Edit", found_index=0)
                if path_input.exists():
                    print("✅ 找到文件名输入框")
                    break
            except:
                pass
            
            # 方法2: 尝试查找地址栏（ComboBox）
            try:
                path_input = file_dialog.child_window(class_name="ComboBox", found_index=0)
                if path_input.exists():
                    print("✅ 找到地址栏")
                    break
            except:
                pass
            
            time.sleep(0.5)
        
        # 在输入框中输入完整文件路径
        if path_input and path_input.exists():
            try:
                path_input.set_text("")  # 清空现有内容
                path_input.type_keys(target_file_path)
                time.sleep(0.5)
                print(f"✅ 已在输入框中输入路径: {target_file_path}")
            except Exception as e:
                print(f"⚠️ 在输入框中输入失败: {e}，尝试直接输入")
                try:
                    file_dialog.type_keys(target_file_path)
                    time.sleep(0.5)
                    print(f"✅ 已在对话框中输入路径")
                except:
                    print(f"❌ 输入路径失败: {e}")
                    return False
        else:
            # 如果找不到输入框，直接在整个对话框中输入路径
            print("⚠️ 无法找到文件路径输入框，尝试直接输入")
            try:
                file_dialog.type_keys(target_file_path)
                time.sleep(0.5)
                print(f"✅ 已在对话框中输入路径: {target_file_path}")
            except Exception as e:
                print(f"❌ 输入路径失败: {e}")
                return False
        
        # 6. 直接按 Enter 键打开文件
        print("按 Enter 键打开文件...")
        try:
            file_dialog.type_keys("{ENTER}")
            time.sleep(2)  # 等待文件加载
            print("✅ 已按 Enter 键，文件已打开")
        except Exception as e:
            print(f"❌ 按 Enter 键打开文件失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 导入文件过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def execute_flash_program_1(app, main_window):
    """
    执行刷写操作
    
    流程：
    1. 点击 Select ALL 按钮（忽略大小写）
    2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
    3. 在窗口中找到搜索框，输入 "DF_UCBS: 24 Kbyte Data Flash 0 UCB"
    4. 找到搜索框旁边的按钮 Enable，勾选 Enable 按钮
    5. 找到 Program 按钮（不是 Program all 按钮），点击 Program 按钮
    
    Args:
        app: pywinauto Application 对象
        main_window: 主窗口对象
    
    Args:
        main_window: 主窗口对象
    
    Returns:
        bool: 刷写操作是否成功
    """
    try:
        # 1. 点击 Select ALL 按钮（忽略大小写）
        print("查找 Select ALL 按钮...")
        select_all_button = None
        max_retries = 10
        
        # 尝试多种可能的按钮标题（忽略大小写）
        button_titles = ["Select All", "Select ALL", "select all", "SELECT ALL", "全选"]
        
        for i in range(max_retries):
            for title in button_titles:
                try:
                    select_all_button = main_window.child_window(class_name="Button", title=title)
                    if select_all_button.exists():
                        print(f"✅ 找到 Select ALL 按钮: {title}")
                        break
                except:
                    pass
            
            if select_all_button and select_all_button.exists():
                break
            time.sleep(0.5)
        
        if not select_all_button or not select_all_button.exists():
            print("❌ 无法找到 Select ALL 按钮")
            return False
        
        print("点击 Select ALL 按钮...")
        select_all_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
        print("验证 Unselect All 按钮是否存在...")
        unselect_all_button = None
        max_retries = 5
        
        for i in range(max_retries):
            try:
                unselect_all_button = main_window.child_window(class_name="Button", title="Unselect All")
                if not unselect_all_button.exists():
                    unselect_all_button = main_window.child_window(class_name="Button", title="取消全选")
                
                if unselect_all_button.exists():
                    print("✅ 找到 Unselect All 按钮，说明 Select ALL 操作成功")
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not unselect_all_button or not unselect_all_button.exists():
            print("⚠️ 未找到 Unselect All 按钮，但继续执行")
        
        # 点击 Add Sel 按钮
        print("查找 Add Sel 按钮...")
        add_sel_button = None
        max_retries = 10
        
        add_sel_titles = ["Add Sel. >>", "Add Sel", "add sel", "ADD SEL"]
        
        for i in range(max_retries):
            for title in add_sel_titles:
                try:
                    add_sel_button = main_window.child_window(class_name="Button", title=title)
                    if add_sel_button.exists():
                        print(f"✅ 找到 Add Sel 按钮: {title}")
                        break
                except:
                    pass
            
            if add_sel_button and add_sel_button.exists():
                break
            time.sleep(0.5)
        
        if not add_sel_button or not add_sel_button.exists():
            print("❌ 无法找到 Add Sel 按钮")
            return False
        
        print("点击 Add Sel 按钮...")
        add_sel_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 3. 在窗口中找到搜索框，清空文本，按"下"键4次，检查内容是否匹配
        print("查找搜索框...")
        search_text = "DF_UCBS: 24 Kbyte Data Flash 0 UCB"
        
        # 搜索框可能是 ComboBox 或 Edit 控件
        search_combo = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 ComboBox（下拉框）
                search_combo = main_window.child_window(class_name="ComboBox", found_index=0)
                if search_combo.exists():
                    print("✅ 找到搜索框（ComboBox）")
                    break
            except:
                pass
            
            # 如果找不到 ComboBox，尝试查找 Edit
            try:
                search_combo = main_window.child_window(class_name="Edit", found_index=0)
                if search_combo.exists():
                    print("✅ 找到搜索框（Edit）")
                    break
            except:
                pass
            
            time.sleep(0.5)
        
        if not search_combo or not search_combo.exists():
            print("❌ 无法找到搜索框")
            return False
        
        # 3. 检查搜索框内容，匹配两种可能的文本
        # 目标文本：1. "DF_UCBS: 24 Kbyte Data Flash 0 UCB"
        #           2. "DF_UCBS: 24 Kbyte Data Flash 0 UCB  (not ready)"
        base_text = "DF_UCBS: 24 Kbyte Data Flash 0 UCB"
        target_texts = [
            "DF_UCBS: 24 Kbyte Data Flash 0 UCB",
            "DF_UCBS: 24 Kbyte Data Flash 0 UCB  (not ready)"
        ]
        
        print(f"检查搜索框内容是否匹配目标文本...")
        matched = False
        matched_text = None
        
        try:
            # 先检查当前搜索框内容
            current_text = search_combo.window_text()
            print(f"  当前搜索框内容: {current_text}")
            
            # 检查是否匹配任一目标文本
            for target in target_texts:
                if current_text == target or target in current_text:
                    print(f"✅ 搜索框内容已匹配: {current_text}")
                    matched = True
                    matched_text = current_text
                    break
            
            if not matched:
                print(f"⚠️ 搜索框内容不匹配，开始按'下'键查找...")
                # 按"下"键，直到匹配任一目标文本（最多5次）
                max_down_keys = 5  # 最多按5次
                for i in range(max_down_keys):
                    search_combo.type_keys("{DOWN}")
                    time.sleep(0.2)  # 每次按键后稍作等待
                    
                    # 再次检查搜索框内容
                    try:
                        current_text = search_combo.window_text()
                        print(f"  第 {i+1} 次按键，当前内容: {current_text}")
                        
                        # 检查是否匹配任一目标文本
                        for target in target_texts:
                            if current_text == target or target in current_text:
                                print(f"✅ 搜索框内容匹配（第 {i+1} 次按键后）: {current_text}")
                                matched = True
                                matched_text = current_text
                                break
                        
                        if matched:
                            break
                    except Exception as e:
                        print(f"  第 {i+1} 次按键，无法读取内容: {e}")
                
                if not matched:
                    print(f"❌ 按了 {max_down_keys} 次'下'键后仍未匹配到目标内容")
                    return False
        except Exception as e:
            print(f"❌ 检查搜索框内容失败: {e}")
            return False
        
        # 4. 根据匹配的文本决定是否点击 Enable 按钮
        if matched_text and "(not ready)" in matched_text:
            # 如果包含 "(not ready)"，需要点击 Enable 按钮
            print("⚠️ 匹配的文本包含 '(not ready)'，需要点击 Enable 按钮")
            
            # 查找 Enable 按钮
            print("查找 Enable 按钮...")
            enable_button = None
            max_retries = 10
            
            for i in range(max_retries):
                try:
                    # Enable 可能是 Button 或 CheckBox
                    enable_button = main_window.child_window(class_name="Button", title="Enable")
                    if not enable_button.exists():
                        enable_button = main_window.child_window(class_name="CheckBox", title="Enable")
                    
                    if enable_button.exists():
                        print("✅ 找到 Enable 按钮")
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not enable_button or not enable_button.exists():
                print("❌ 无法找到 Enable 按钮")
                return False
            
            # 点击 Enable 按钮
            print("点击 Enable 按钮...")
            try:
                enable_button.click()
                time.sleep(0.5)
                print("✅ 已点击 Enable 按钮")
            except Exception as e:
                print(f"❌ 点击 Enable 按钮失败: {e}")
                return False
            
            # 点击 Enable 后，再次检查搜索框内容，确认不包含 "(not ready)"
            print("点击 Enable 后，再次检查搜索框内容...")
            try:
                current_text = search_combo.window_text()
                print(f"  当前搜索框内容: {current_text}")
                
                if "(not ready)" in current_text:
                    print("❌ 点击 Enable 后，搜索框内容仍包含 '(not ready)'")
                    return False
                else:
                    print("✅ 点击 Enable 后，搜索框内容已不包含 '(not ready)'，可以继续刷写")
            except Exception as e:
                print(f"⚠️ 无法检查搜索框内容: {e}")
                print("⚠️ 继续执行刷写步骤")
        else:
            # 如果不包含 "(not ready)"，直接进行刷写步骤
            print("✅ 匹配的文本不包含 '(not ready)'，直接进行刷写步骤")
        
        # 5. 找到 Program 按钮（不是 Program all 按钮），点击 Program 按钮开始刷写
        print("查找 Program 按钮（注意：不是 Program all 按钮）...")
        program_button = None
        max_retries = 10
        
        # 尝试精确匹配 "Program"（排除 "Program all"）
        program_titles = ["Program", "刷写"]
        
        for i in range(max_retries):
            for title in program_titles:
                try:
                    # 直接查找标题为 "Program" 的按钮
                    program_button = main_window.child_window(class_name="Button", title=title)
                    
                    if program_button.exists():
                        # 验证不是 Program all 按钮
                        try:
                            btn_text = program_button.window_text()
                            # 检查是否包含 "all" 或 "全部"（排除 Program all）
                            if "all" in btn_text.lower() or "全部" in btn_text:
                                print(f"⚠️ 找到的是 {btn_text} 按钮，跳过")
                                program_button = None  # 重置，继续查找
                                continue
                            else:
                                print(f"✅ 找到 Program 按钮: {btn_text}")
                                break
                        except:
                            # 如果无法获取文本，假设是正确的按钮
                            print(f"✅ 找到 Program 按钮: {title}")
                            break
                except:
                    pass
            
            if program_button and program_button.exists():
                break
            time.sleep(0.5)
        
        if not program_button or not program_button.exists():
            print("❌ 无法找到 Program 按钮")
            return False
        
        # 最终验证：确保不是 Program all 按钮
        try:
            btn_text = program_button.window_text()
            if "all" in btn_text.lower() or "全部" in btn_text:
                print(f"❌ 错误：找到的是 {btn_text} 按钮，不是 Program 按钮")
                return False
        except:
            pass
        
        print("点击 Program 按钮开始刷写...")
        program_button.click()
        time.sleep(1)
        print("✅ 已点击 Program 按钮，刷写已开始")
        
        # 6. 等待刷写完成，监控刷写窗口
        print("等待刷写窗口弹出...")
        flash_window = None
        max_wait_window = 15  # 最多等待15秒让窗口弹出
        
        # 多种方法查找 "Execute Memtool Command" 窗口
        for i in range(max_wait_window):
            try:
                # 方法1: 直接通过标题查找窗口
                try:
                    flash_window = app.window(title="Execute Memtool Command")
                    if flash_window.exists() and flash_window.is_visible():
                        print(f"✅ 找到刷写窗口: {flash_window.window_text()}")
                        break
                except:
                    pass
                
                
            except Exception as e:
                print(f"⚠️ 查找窗口时出错: {e}")
            
            if flash_window:
                break
            
            print(f"  等待窗口弹出... ({i+1}/{max_wait_window})")
            time.sleep(1)
        
        if not flash_window:
            print("❌ 未找到刷写窗口 'Execute Memtool Command'")
            print("⚠️ 尝试列出所有可见窗口...")
            try:
                all_windows = app.windows()
                for win in all_windows:
                    try:
                        if win.exists() and win.is_visible():
                            print(f"  可见窗口: {win.window_text()}")
                    except:
                        pass
            except:
                pass
            return False
        
        # 监控刷写进度和结果
        print("监控刷写进度和结果...")
        max_wait_time = 120  # 最多等待60秒
        check_interval = 0.5  # 每0.5秒检查一次
        start_time = time.time()
        success_found = False
        failed_found = False
        
        while time.time() - start_time < max_wait_time:
            try:
                #  尝试查找 result 相关的控件，检查是否包含 "success" 或 "failed"
                try:
                    # 查找所有文本控件，检查是否包含 success 或 failed
                    all_texts = []
                    try:
                        # 尝试获取窗口中的所有文本
                        descendants = flash_window.descendants()
                        for desc in descendants:
                            try:
                                text = desc.window_text()
                                if text:
                                    all_texts.append(text.lower())
                            except:
                                pass
                    except:
                        pass
                    
                    # 检查是否包含 success 或 failed
                    for text in all_texts:
                        if "success" in text:
                            print(f"✅ 检测到 success: {text}")
                            success_found = True
                            break
                        elif "failed" in text or "fail" in text:
                            print(f"❌ 检测到 failed: {text}")
                            failed_found = True
                            break
                    
                    if success_found:
                        break
                    if failed_found:
                        return False
                except:
                    pass

            except Exception as e:
                print(f"⚠️ 检查刷写状态时出错: {e}")
            
            time.sleep(check_interval)
        
        # 检查结果
        if failed_found:
            print("❌ 刷写失败：检测到 failed")
            return False
        
        if not success_found:
            print(f"❌ 刷写超时：{max_wait_time} 秒内未检测到 success")
            return False
        
        # 找到 success 后，点击 EXIT 按钮退出窗口
        print("查找 EXIT 按钮...")
        exit_button = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 EXIT 按钮
                exit_titles = ["Exit", "EXIT"]
                for title in exit_titles:
                    try:
                        exit_button = flash_window.child_window(class_name="Button", title=title)
                        if exit_button.exists():
                            print(f"✅ 找到 EXIT 按钮: {title}")
                            break
                    except:
                        pass
                
                if exit_button and exit_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not exit_button or not exit_button.exists():
            print("⚠️ 无法找到 EXIT 按钮")
        else:
            print("点击 EXIT 按钮退出刷写窗口...")
            try:
                exit_button.click()
                time.sleep(1)
                print("✅ 已点击 EXIT 按钮")
                
                # 验证是否真的退出了刷写窗口
                print("验证刷写窗口是否已关闭...")
                try:
                    if not flash_window.exists() or not flash_window.is_visible():
                        print("✅ 刷写窗口已成功关闭")
                    else:
                        print("⚠️ 刷写窗口似乎仍存在")
                        # 再次尝试点击 EXIT
                        if exit_button.exists():
                            print("尝试再次点击 EXIT...")
                            exit_button.click()
                            time.sleep(1)
                except:
                    print("✅ 刷写窗口已关闭")
                    
            except Exception as e:
                print(f"⚠️ 点击 EXIT 按钮失败: {e}")
        
        print("✅ HSM刷写完成")
        return True

    except Exception as e:
        print(f"❌ 刷写操作过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False    

def execute_flash_program_2(app, main_window):
    """
    执行刷写操作
    
    流程：
    3. 在窗口中找到搜索框，输入 "DF1: 128 KByte OnChip Data FLASH 1"
    4. 找到搜索框旁边的按钮 Enable，勾选 Enable 按钮
    5. 找到 Program 按钮（不是 Program all 按钮），点击 Program 按钮
    
    Args:
        app: pywinauto Application 对象
        main_window: 主窗口对象
    
    Args:
        main_window: 主窗口对象
    
    Returns:
        bool: 刷写操作是否成功
    """
    try:
        # 3. 在窗口中找到搜索框，执行复杂的查找逻辑
        print("查找搜索框...")
        
        # 搜索框可能是 ComboBox 或 Edit 控件
        search_combo = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 ComboBox（下拉框）
                search_combo = main_window.child_window(class_name="ComboBox", found_index=0)
                if search_combo.exists():
                    print("✅ 找到搜索框（ComboBox）")
                    break
            except:
                pass
            
            # 如果找不到 ComboBox，尝试查找 Edit
            try:
                search_combo = main_window.child_window(class_name="Edit", found_index=0)
                if search_combo.exists():
                    print("✅ 找到搜索框（Edit）")
                    break
            except:
                pass
            
            time.sleep(0.5)
        
        if not search_combo or not search_combo.exists():
            print("❌ 无法找到搜索框")
            return False
        
        # 目标文本
        target_df1 = [
            "DF1: 128 KByte OnChip Data FLASH 1",
            "DF1: 128 KByte OnChip Data FLASH 1  (not ready)"
        ]
        target_df_ucbs = [
            "DF_UCBS: 24 Kbyte Data Flash 0 UCB",
            "DF_UCBS: 24 Kbyte Data Flash 0 UCB  (not ready)"
        ]
        
        print("开始执行搜索逻辑...")
        matched = False
        matched_text = None
        
        # 步骤 A: 按一下上键，匹配 DF1
        print("步骤 A: 按一下上键，尝试匹配 DF1...")
        try:
            search_combo.type_keys("{UP}")
            time.sleep(0.5)
            current_text = search_combo.window_text()
            print(f"  当前内容: {current_text}")
            
            for target in target_df1:
                if current_text == target or target in current_text:
                    print(f"✅ 匹配到 DF1: {current_text}")
                    matched = True
                    matched_text = current_text
                    break
        except Exception as e:
            print(f"⚠️ 步骤 A 出错: {e}")
            
        # 步骤 B: 如果未匹配，按5次下键匹配 DF_UCBS，再按一次上键匹配 DF1
        if not matched:
            print("步骤 B: 未匹配到 DF1，尝试按5次下键查找 DF_UCBS...")
            ucbs_found = False
            
            # 按5次下键查找 DF_UCBS
            for i in range(5):
                try:
                    search_combo.type_keys("{DOWN}")
                    time.sleep(0.2)
                    current_text = search_combo.window_text()
                    print(f"  第 {i+1} 次下键，当前内容: {current_text}")
                    
                    for target in target_df_ucbs:
                        if current_text == target or target in current_text:
                            print(f"✅ 找到 DF_UCBS: {current_text}")
                            ucbs_found = True
                            break
                    if ucbs_found:
                        break
                except Exception as e:
                    print(f"  第 {i+1} 次下键出错: {e}")
            
            if ucbs_found:
                print("找到 DF_UCBS 后，按一次上键去匹配 DF1...")
                try:
                    search_combo.type_keys("{UP}")
                    time.sleep(0.5)
                    current_text = search_combo.window_text()
                    print(f"  当前内容: {current_text}")
                    
                    for target in target_df1:
                        if current_text == target or target in current_text:
                            print(f"✅ 最终匹配到 DF1: {current_text}")
                            matched = True
                            matched_text = current_text
                            break
                except Exception as e:
                    print(f"⚠️ 按上键出错: {e}")
            else:
                print("❌ 未能找到 DF_UCBS，无法继续")
                return False
        
        if not matched:
            print("❌ 最终未能匹配到 DF1")
            return False
            
        # 4. 根据匹配内容执行操作
        # 如果为 DF1... (Ready)，则点击 Enable
        # 如果带了 (not ready)，则识别 Erase 按钮并点击
        #点击完Erase按钮后，会有新窗口弹出，窗口标题是“Selct FALSH Sectors to Erase - DF1”
        #在新窗口中，找到“Start”按钮，点击“Start”按钮，开始擦除
        if "(not ready)" in matched_text:
            print("⚠️ 匹配内容包含 '(not ready)'，执行 Enable -> Erase 流程")
            
            # 1. 查找并点击 Enable 按钮
            print("查找 Enable 按钮...")
            enable_button = None
            max_retries = 10
            for i in range(max_retries):
                try:
                    enable_button = main_window.child_window(class_name="Button", title="Enable")
                    if not enable_button.exists():
                        enable_button = main_window.child_window(class_name="CheckBox", title="Enable")
                    
                    if enable_button.exists():
                        print("✅ 找到 Enable 按钮")
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not enable_button or not enable_button.exists():
                print("❌ 无法找到 Enable 按钮")
                return False
            
            print("点击 Enable 按钮...")
            try:
                enable_button.click()
                time.sleep(1)
                print("✅ 已点击 Enable 按钮")
            except Exception as e:
                print(f"❌ 点击 Enable 按钮失败: {e}")
                return False
            
            # 2. 验证文本内容不再包含 (not ready)
            print("验证搜索框内容是否变为 Ready...")
            try:
                current_text = search_combo.window_text()
                print(f"  当前搜索框内容: {current_text}")
                
                if "(not ready)" in current_text:
                    print("❌ 点击 Enable 后，搜索框内容仍包含 '(not ready)'")
                    return False
                else:
                    print("✅ 点击 Enable 后，搜索框内容已不包含 '(not ready)'")
            except Exception as e:
                print(f"⚠️ 无法检查搜索框内容: {e}")
            
            # 3. 查找 Erase 按钮
            print("查找 Erase 按钮...")
            erase_button = None
            max_retries = 10
            # 尝试多种标题，包括模糊匹配
            erase_titles = ["Erase", "Erase ...", "Erase..."]
            
            for i in range(max_retries):
                # 1. 尝试精确匹配标题
                for title in erase_titles:
                    try:
                        erase_button = main_window.child_window(class_name="Button", title=title)
                        if erase_button.exists():
                            print(f"✅ 找到 Erase 按钮: {title}")
                            break
                    except:
                        pass
                if erase_button and erase_button.exists():
                    break
                
                # 2. 尝试正则模糊匹配 (包含 Erase 的按钮)
                try:
                    erase_button = main_window.child_window(class_name="Button", title_re=".*Erase.*")
                    if erase_button.exists():
                        print(f"✅ 找到 Erase 按钮 (正则): {erase_button.window_text()}")
                        break
                except:
                    pass
                
                time.sleep(0.5)
            
            if not erase_button or not erase_button.exists():
                print("❌ 无法找到 Erase 按钮")
                return False
            
            print("点击 Erase 按钮 (启动刷写)...")
            erase_button.click()
            time.sleep(1)
            print("✅ 已点击 Erase 按钮")
            
            # 4.1 等待 "Select FLASH Sectors to Erase - DF1" 窗口弹出
            print("等待 'Select FLASH Sectors to Erase - DF1' 窗口弹出...")
            erase_window = None
            max_wait_window = 10
            
            for i in range(max_wait_window):
                try:
                    # 尝试通过标题查找窗口
                    erase_window = app.window(title_re=".*Select FLASH Sectors to Erase.*")
                    if erase_window.exists() and erase_window.is_visible():
                        print(f"✅ 找到 Erase 确认窗口: {erase_window.window_text()}")
                        break
                except:
                    pass
                time.sleep(1)
            
            if not erase_window:
                print("❌ 未找到 Erase 确认窗口")
                return False
            
            # 4.2 在新窗口中找到 "Start" 按钮并点击
            print("查找 Start 按钮...")
            start_button = None
            max_retries = 10
            start_titles = ["Start"]
            
            for i in range(max_retries):
                for title in start_titles:
                    try:
                        start_button = erase_window.child_window(class_name="Button", title=title)
                        if start_button.exists():
                            print(f"✅ 找到 Start 按钮: {title}")
                            break
                    except:
                        pass
                if start_button and start_button.exists():
                    break
                time.sleep(0.5)
            
            if not start_button or not start_button.exists():
                print("❌ 无法找到 Start 按钮")
                return False
            
            print("点击 Start 按钮开始擦除...")
            start_button.click()
            time.sleep(1)
            print("✅ 已点击 Start 按钮")
            
        else:
            print("✅ 匹配内容不含 '(not ready)'，执行 Erase 流程")
            
            print("查找 Erase 按钮...")
            erase_button = None
            max_retries = 10
            # 尝试多种标题，包括模糊匹配
            erase_titles = ["Erase", "Erase ...", "Erase..."]
            
            for i in range(max_retries):
                # 1. 尝试精确匹配标题
                for title in erase_titles:
                    try:
                        erase_button = main_window.child_window(class_name="Button", title=title)
                        if erase_button.exists():
                            print(f"✅ 找到 Erase 按钮: {title}")
                            break
                    except:
                        pass
                if erase_button and erase_button.exists():
                    break
                
                # 2. 尝试正则模糊匹配 (包含 Erase 的按钮)
                try:
                    erase_button = main_window.child_window(class_name="Button", title_re=".*Erase.*")
                    if erase_button.exists():
                        print(f"✅ 找到 Erase 按钮 (正则): {erase_button.window_text()}")
                        break
                except:
                    pass
                
                time.sleep(0.5)
            
            if not erase_button or not erase_button.exists():
                print("❌ 无法找到 Erase 按钮")
                return False
            
            print("点击 Erase 按钮 (启动刷写)...")
            erase_button.click()
            time.sleep(1)
            print("✅ 已点击 Erase 按钮")
            
            # 4.1 等待 "Select FLASH Sectors to Erase - DF1" 窗口弹出
            print("等待 'Select FLASH Sectors to Erase - DF1' 窗口弹出...")
            erase_window = None
            max_wait_window = 10
            
            for i in range(max_wait_window):
                try:
                    # 尝试通过标题查找窗口
                    erase_window = app.window(title_re=".*Select FLASH Sectors to Erase.*")
                    if erase_window.exists() and erase_window.is_visible():
                        print(f"✅ 找到 Erase 确认窗口: {erase_window.window_text()}")
                        break
                except:
                    pass
                time.sleep(1)
            
            if not erase_window:
                print("❌ 未找到 Erase 确认窗口")
                return False
            
            # 4.2 在新窗口中找到 "Start" 按钮并点击
            print("查找 Start 按钮...")
            start_button = None
            max_retries = 10
            start_titles = ["Start", "开始"]
            
            for i in range(max_retries):
                for title in start_titles:
                    try:
                        start_button = erase_window.child_window(class_name="Button", title=title)
                        if start_button.exists():
                            print(f"✅ 找到 Start 按钮: {title}")
                            break
                    except:
                        pass
                if start_button and start_button.exists():
                    break
                time.sleep(0.5)
            
            if not start_button or not start_button.exists():
                print("❌ 无法找到 Start 按钮")
                return False
            
            print("点击 Start 按钮开始擦除...")
            start_button.click()
            time.sleep(1)
            print("✅ 已点击 Start 按钮")
                
        # 6. 等待刷写完成，监控刷写窗口
        print("等待刷写窗口弹出...")
        flash_window = None
        max_wait_window = 15  # 最多等待15秒让窗口弹出
        
        # 查找 "Execute Memtool Command" 窗口
        for i in range(max_wait_window):
            try:
                    flash_window = app.window(title="Execute Memtool Command")
                    if flash_window.exists() and flash_window.is_visible():
                        print(f"✅ 找到刷写窗口: {flash_window.window_text()}")
                        break
                
            except Exception as e:
                print(f"⚠️ 查找窗口时出错: {e}")
            
            if flash_window:
                break
            
            print(f"  等待窗口弹出... ({i+1}/{max_wait_window})")
            time.sleep(1)
        
        if not flash_window:
            print("❌ 未找到刷写窗口 'Execute Memtool Command'")
            print("⚠️ 尝试列出所有可见窗口...")
            try:
                all_windows = app.windows()
                for win in all_windows:
                    try:
                        if win.exists() and win.is_visible():
                            print(f"  可见窗口: {win.window_text()}")
                    except:
                        pass
            except:
                pass
            return False
        
        # 监控刷写进度和结果
        print("监控刷写进度和结果...")
        max_wait_time = 120  # 最多等待60秒
        check_interval = 0.5  # 每0.5秒检查一次
        start_time = time.time()
        success_found = False
        failed_found = False
        
        while time.time() - start_time < max_wait_time:
            try:
                # 方法1: 尝试查找 result 相关的控件，检查是否包含 "success" 或 "failed"
                try:
                    # 查找所有文本控件，检查是否包含 success 或 failed
                    all_texts = []
                    try:
                        # 尝试获取窗口中的所有文本
                        descendants = flash_window.descendants()
                        for desc in descendants:
                            try:
                                text = desc.window_text()
                                if text:
                                    all_texts.append(text.lower())
                            except:
                                pass
                    except:
                        pass
                    
                    # 检查是否包含 success 或 failed
                    for text in all_texts:
                        if "success" in text:
                            print(f"✅ 检测到 success: {text}")
                            success_found = True
                            break
                        elif "failed" in text or "fail" in text:
                            print(f"❌ 检测到 failed: {text}")
                            failed_found = True
                            break
                    
                    if success_found:
                        break
                    if failed_found:
                        return False
                except:
                    pass
            except Exception as e:
                print(f"⚠️ 检查刷写状态时出错: {e}")    
            
            time.sleep(check_interval)
        
        # 检查结果
        if failed_found:
            print("❌ 刷写失败：检测到 failed")
            return False
        
        if not success_found:
            print(f"❌ 刷写超时：{max_wait_time} 秒内未检测到 success")
            return False
        
        # 找到 success 后，点击 EXIT 按钮退出窗口
        print("查找 EXIT 按钮...")
        exit_button = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 EXIT 按钮
                exit_titles = ["Exit", "EXIT"]
                for title in exit_titles:
                    try:
                        exit_button = flash_window.child_window(class_name="Button", title=title)
                        if exit_button.exists():
                            print(f"✅ 找到 EXIT 按钮: {title}")
                            break
                    except:
                        pass
                
                if exit_button and exit_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not exit_button or not exit_button.exists():
            print("⚠️ 无法找到 EXIT 按钮")
        else:
            print("点击 EXIT 按钮退出刷写窗口...")
            try:
                exit_button.click()
                time.sleep(1)
                print("✅ 已点击 EXIT 按钮")
                
                # 验证是否真的退出了刷写窗口
                print("验证刷写窗口是否已关闭...")
                try:
                    if not flash_window.exists() or not flash_window.is_visible():
                        print("✅ 刷写窗口已成功关闭")
                    else:
                        print("⚠️ 刷写窗口似乎仍存在")
                        # 再次尝试点击 EXIT
                        if exit_button.exists():
                            print("尝试再次点击 EXIT...")
                            exit_button.click()
                            time.sleep(1)
                except:
                    print("✅ 刷写窗口已关闭")
                    
            except Exception as e:
                print(f"⚠️ 点击 EXIT 按钮失败: {e}")
        
        print("✅ HSM擦除完成")
        return True

        
    except Exception as e:
        print(f"❌ 刷写操作过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def execute_flash_program_3(app, main_window):
    """
    执行刷写操作
    
    流程：
    1. 点击 Select ALL 按钮（忽略大小写）
    2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
    3. 找到Program all按钮(不是Program按钮)，点击 Program all按钮
    
    Args:
        app: pywinauto Application 对象
        main_window: 主窗口对象
    
    Args:
        main_window: 主窗口对象
    
    Returns:
        bool: 刷写操作是否成功
    """
    try:
        # 1. 点击 Select ALL 按钮（忽略大小写）
        print("查找 Select ALL 按钮...")
        select_all_button = None
        max_retries = 10
        
        # 尝试多种可能的按钮标题（忽略大小写）
        button_titles = ["Select All", "Select ALL", "select all", "SELECT ALL"]
        
        for i in range(max_retries):
            for title in button_titles:
                try:
                    select_all_button = main_window.child_window(class_name="Button", title=title)
                    if select_all_button.exists():
                        print(f"✅ 找到 Select ALL 按钮: {title}")
                        break
                except:
                    pass
            
            if select_all_button and select_all_button.exists():
                break
            time.sleep(0.5)
        
        if not select_all_button or not select_all_button.exists():
            print("❌ 无法找到 Select ALL 按钮")
            return False
        
        print("点击 Select ALL 按钮...")
        select_all_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
        print("验证 Unselect All 按钮是否存在...")
        unselect_all_button = None
        max_retries = 5
        
        for i in range(max_retries):
            try:
                unselect_all_button = main_window.child_window(class_name="Button", title="Unselect All")
                if not unselect_all_button.exists():
                    unselect_all_button = main_window.child_window(class_name="Button", title="取消全选")
                
                if unselect_all_button.exists():
                    print("✅ 找到 Unselect All 按钮，说明 Select ALL 操作成功")
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not unselect_all_button or not unselect_all_button.exists():
            print("⚠️ 未找到 Unselect All 按钮，但继续执行")
        
        # 点击 Add Sel 按钮
        print("查找 Add Sel 按钮...")
        add_sel_button = None
        max_retries = 10
        
        add_sel_titles = ["Add Sel. >>", "Add Sel", "add sel", "ADD SEL"]
        
        for i in range(max_retries):
            for title in add_sel_titles:
                try:
                    add_sel_button = main_window.child_window(class_name="Button", title=title)
                    if add_sel_button.exists():
                        print(f"✅ 找到 Add Sel 按钮: {title}")
                        break
                except:
                    pass
            
            if add_sel_button and add_sel_button.exists():
                break
            time.sleep(0.5)
        
        if not add_sel_button or not add_sel_button.exists():
            print("❌ 无法找到 Add Sel 按钮")
            return False
        
        print("点击 Add Sel 按钮...")
        add_sel_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 5. 找到 Program All 按钮（不是 Program 按钮），点击开始刷写
        print("查找 Program All 按钮...")
        program_all_button = None
        max_retries = 10
        
        # 尝试精确匹配 "Program all" (不区分大小写)
        program_all_titles = ["Program All", "Program all"]
        
        for i in range(max_retries):
            for title in program_all_titles:
                try:
                    # 查找按钮
                    btn = main_window.child_window(class_name="Button", title=title)
                    
                    if btn.exists():
                        # 验证确实是 Program All (包含 "all" 或 "全部")
                        try:
                            btn_text = btn.window_text()
                            if "all" in btn_text.lower() or "全部" in btn_text:
                                print(f"✅ 找到 Program All 按钮: {btn_text}")
                                program_all_button = btn
                                break
                            else:
                                print(f"⚠️ 找到的是 {btn_text} 按钮，不是 Program All，跳过")
                        except:
                            # 如果无法获取文本，但标题匹配，暂且认为是
                            print(f"✅ 找到 Program All 按钮: {title}")
                            program_all_button = btn
                            break
                except:
                    pass
            
            if program_all_button and program_all_button.exists():
                break
            time.sleep(0.5)
        
        if not program_all_button or not program_all_button.exists():
            print("❌ 无法找到 Program All 按钮")
            return False
        
        print("点击 Program All 按钮开始刷写...")
        program_all_button.click()
        time.sleep(1)
        print("✅ 已点击 Program All 按钮，刷写已开始")
        
        # 6. 等待刷写完成，监控刷写窗口
        print("等待刷写窗口弹出...")
        flash_window = None
        max_wait_window = 15  # 最多等待15秒让窗口弹出
        
        # 多种方法查找 "Execute Memtool Command" 窗口
        for i in range(max_wait_window):
            try:
                #  直接通过标题查找窗口
                try:
                    flash_window = app.window(title="Execute Memtool Command")
                    if flash_window.exists() and flash_window.is_visible():
                        print(f"✅ 找到刷写窗口: {flash_window.window_text()}")
                        break
                except:
                    pass
                
                
            except Exception as e:
                print(f"⚠️ 查找窗口时出错: {e}")
            
            if flash_window:
                break
            
            print(f"  等待窗口弹出... ({i+1}/{max_wait_window})")
            time.sleep(1)
        
        if not flash_window:
            print("❌ 未找到刷写窗口 'Execute Memtool Command'")
            print("⚠️ 尝试列出所有可见窗口...")
            try:
                all_windows = app.windows()
                for win in all_windows:
                    try:
                        if win.exists() and win.is_visible():
                            print(f"  可见窗口: {win.window_text()}")
                    except:
                        pass
            except:
                pass
            return False
        
        # 监控刷写进度和结果
        print("监控刷写进度和结果...")
        max_wait_time = 120  # 最多等待60秒
        check_interval = 0.5  # 每0.5秒检查一次
        start_time = time.time()
        success_found = False
        failed_found = False
        
        while time.time() - start_time < max_wait_time:
            try:
                # 方法1: 尝试查找 result 相关的控件，检查是否包含 "success" 或 "failed"
                try:
                    # 查找所有文本控件，检查是否包含 success 或 failed
                    all_texts = []
                    try:
                        # 尝试获取窗口中的所有文本
                        descendants = flash_window.descendants()
                        for desc in descendants:
                            try:
                                text = desc.window_text()
                                if text:
                                    all_texts.append(text.lower())
                            except:
                                pass
                    except:
                        pass
                    
                    # 检查是否包含 success 或 failed
                    for text in all_texts:
                        if "success" in text:
                            print(f"✅ 检测到 success: {text}")
                            success_found = True
                            break
                        elif "failed" in text or "fail" in text:
                            print(f"❌ 检测到 failed: {text}")
                            failed_found = True
                            break
                    
                    if success_found:
                        break
                    if failed_found:
                        return False
                except:
                    pass
                
                # 方法2: 尝试直接查找包含 "success" 或 "failed" 的控件
                try:
                    success_control = flash_window.child_window(title_re=".*success.*", found_index=0)
                    if success_control.exists():
                        print("✅ 找到 success 控件")
                        success_found = True
                        break
                except:
                    pass
                
                try:
                    failed_control = flash_window.child_window(title_re=".*failed.*", found_index=0)
                    if failed_control.exists():
                        print("❌ 找到 failed 控件")
                        failed_found = True
                        return False
                except:
                    pass
            
            except Exception as e:
                print(f"⚠️ 检查刷写状态时出错: {e}")
            
            time.sleep(check_interval)
        
        # 检查结果
        if failed_found:
            print("❌ 刷写失败：检测到 failed")
            return False
        
        if not success_found:
            print(f"❌ 刷写超时：{max_wait_time} 秒内未检测到 success")
            return False
        
        # 找到 success 后，点击 EXIT 按钮退出窗口
        print("查找 EXIT 按钮...")
        exit_button = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 EXIT 按钮
                exit_titles = ["Exit", "EXIT"]
                for title in exit_titles:
                    try:
                        exit_button = flash_window.child_window(class_name="Button", title=title)
                        if exit_button.exists():
                            print(f"✅ 找到 EXIT 按钮: {title}")
                            break
                    except:
                        pass
                
                if exit_button and exit_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not exit_button or not exit_button.exists():
            print("⚠️ 无法找到 EXIT 按钮")
        else:
            print("点击 EXIT 按钮退出刷写窗口...")
            try:
                exit_button.click()
                time.sleep(1)
                print("✅ 已点击 EXIT 按钮")
                
                # 验证是否真的退出了刷写窗口
                print("验证刷写窗口是否已关闭...")
                try:
                    if not flash_window.exists() or not flash_window.is_visible():
                        print("✅ 刷写窗口已成功关闭")
                    else:
                        print("⚠️ 刷写窗口似乎仍存在")
                        # 再次尝试点击 EXIT
                        if exit_button.exists():
                            print("尝试再次点击 EXIT...")
                            exit_button.click()
                            time.sleep(1)
                except:
                    print("✅ 刷写窗口已关闭")
                    
            except Exception as e:
                print(f"⚠️ 点击 EXIT 按钮失败: {e}")
        
        print("✅ AB文件刷写完成")
        return True

    except Exception as e:
        print(f"❌ 刷写操作过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def execute_flash_program_4(app, main_window):
    """
    执行刷写操作
    
    流程：
    1. 点击 Select ALL 按钮（忽略大小写）
    2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
    3. 找到Program all按钮(不是Program按钮)，点击 Program all按钮
    
    Args:
        app: pywinauto Application 对象
        main_window: 主窗口对象
    
    Args:
        main_window: 主窗口对象
    
    Returns:
        bool: 刷写操作是否成功
    """
    try:
        # 1. 点击 Select ALL 按钮（忽略大小写）
        print("查找 Select ALL 按钮...")
        select_all_button = None
        max_retries = 10
        
        # 尝试多种可能的按钮标题（忽略大小写）
        button_titles = ["Select All", "Select ALL", "select all", "SELECT ALL"]
        
        for i in range(max_retries):
            for title in button_titles:
                try:
                    select_all_button = main_window.child_window(class_name="Button", title=title)
                    if select_all_button.exists():
                        print(f"✅ 找到 Select ALL 按钮: {title}")
                        break
                except:
                    pass
            
            if select_all_button and select_all_button.exists():
                break
            time.sleep(0.5)
        
        if not select_all_button or not select_all_button.exists():
            print("❌ 无法找到 Select ALL 按钮")
            return False
        
        print("点击 Select ALL 按钮...")
        select_all_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 2. 识别到有 Unselect All 按钮后，点击 Add Sel 按钮
        print("验证 Unselect All 按钮是否存在...")
        unselect_all_button = None
        max_retries = 5
        
        for i in range(max_retries):
            try:
                unselect_all_button = main_window.child_window(class_name="Button", title="Unselect All")
                if not unselect_all_button.exists():
                    unselect_all_button = main_window.child_window(class_name="Button", title="取消全选")
                
                if unselect_all_button.exists():
                    print("✅ 找到 Unselect All 按钮，说明 Select ALL 操作成功")
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not unselect_all_button or not unselect_all_button.exists():
            print("⚠️ 未找到 Unselect All 按钮，但继续执行")
        
        # 点击 Add Sel 按钮
        print("查找 Add Sel 按钮...")
        add_sel_button = None
        max_retries = 10
        
        add_sel_titles = ["Add Sel. >>", "Add Sel", "add sel", "ADD SEL"]
        
        for i in range(max_retries):
            for title in add_sel_titles:
                try:
                    add_sel_button = main_window.child_window(class_name="Button", title=title)
                    if add_sel_button.exists():
                        print(f"✅ 找到 Add Sel 按钮: {title}")
                        break
                except:
                    pass
            
            if add_sel_button and add_sel_button.exists():
                break
            time.sleep(0.5)
        
        if not add_sel_button or not add_sel_button.exists():
            print("❌ 无法找到 Add Sel 按钮")
            return False
        
        print("点击 Add Sel 按钮...")
        add_sel_button.click()
        time.sleep(1)  # 等待操作完成
        
        # 5. 找到 Program All 按钮（不是 Program 按钮），点击开始刷写
        print("查找 Program All 按钮...")
        program_all_button = None
        max_retries = 10
        
        # 尝试精确匹配 "Program all" (不区分大小写)
        program_all_titles = ["Program All", "Program all"]
        
        for i in range(max_retries):
            for title in program_all_titles:
                try:
                    # 查找按钮
                    btn = main_window.child_window(class_name="Button", title=title)
                    
                    if btn.exists():
                        # 验证确实是 Program All (包含 "all" 或 "全部")
                        try:
                            btn_text = btn.window_text()
                            if "all" in btn_text.lower() or "全部" in btn_text:
                                print(f"✅ 找到 Program All 按钮: {btn_text}")
                                program_all_button = btn
                                break
                            else:
                                print(f"⚠️ 找到的是 {btn_text} 按钮，不是 Program All，跳过")
                        except:
                            # 如果无法获取文本，但标题匹配，暂且认为是
                            print(f"✅ 找到 Program All 按钮: {title}")
                            program_all_button = btn
                            break
                except:
                    pass
            
            if program_all_button and program_all_button.exists():
                break
            time.sleep(0.5)
        
        if not program_all_button or not program_all_button.exists():
            print("❌ 无法找到 Program All 按钮")
            return False
        
        print("点击 Program All 按钮开始刷写...")
        program_all_button.click()
        time.sleep(1)
        print("✅ 已点击 Program All 按钮，刷写已开始")
        
        # 6. 等待刷写完成，监控刷写窗口
        print("等待刷写窗口弹出...")
        flash_window = None
        max_wait_window = 15  # 最多等待15秒让窗口弹出
        
        # 多种方法查找 "Execute Memtool Command" 窗口
        for i in range(max_wait_window):
            try:
                # 直接通过标题查找窗口
                try:
                    flash_window = app.window(title="Execute Memtool Command")
                    if flash_window.exists() and flash_window.is_visible():
                        print(f"✅ 找到刷写窗口: {flash_window.window_text()}")
                        break
                except:
                    pass
                
                
            except Exception as e:
                print(f"⚠️ 查找窗口时出错: {e}")
            
            if flash_window:
                break
            
            print(f"  等待窗口弹出... ({i+1}/{max_wait_window})")
            time.sleep(1)
        
        if not flash_window:
            print("❌ 未找到刷写窗口 'Execute Memtool Command'")
            print("⚠️ 尝试列出所有可见窗口...")
            try:
                all_windows = app.windows()
                for win in all_windows:
                    try:
                        if win.exists() and win.is_visible():
                            print(f"  可见窗口: {win.window_text()}")
                    except:
                        pass
            except:
                pass
            return False
        
        # 监控刷写进度和结果
        print("监控刷写进度和结果...")
        max_wait_time = 120  # 最多等待60秒
        check_interval = 0.5  # 每0.5秒检查一次
        start_time = time.time()
        success_found = False
        failed_found = False
        
        while time.time() - start_time < max_wait_time:
            try:
                # 方法1: 尝试查找 result 相关的控件，检查是否包含 "success" 或 "failed"
                try:
                    # 查找所有文本控件，检查是否包含 success 或 failed
                    all_texts = []
                    try:
                        # 尝试获取窗口中的所有文本
                        descendants = flash_window.descendants()
                        for desc in descendants:
                            try:
                                text = desc.window_text()
                                if text:
                                    all_texts.append(text.lower())
                            except:
                                pass
                    except:
                        pass
                    
                    # 检查是否包含 success 或 failed
                    for text in all_texts:
                        if "success" in text:
                            print(f"✅ 检测到 success: {text}")
                            success_found = True
                            break
                        elif "failed" in text or "fail" in text:
                            print(f"❌ 检测到 failed: {text}")
                            failed_found = True
                            break
                    
                    if success_found:
                        break
                    if failed_found:
                        return False
                except:
                    pass
                
                # 方法2: 尝试直接查找包含 "success" 或 "failed" 的控件
                try:
                    success_control = flash_window.child_window(title_re=".*success.*", found_index=0)
                    if success_control.exists():
                        print("✅ 找到 success 控件")
                        success_found = True
                        break
                except:
                    pass
                
                try:
                    failed_control = flash_window.child_window(title_re=".*failed.*", found_index=0)
                    if failed_control.exists():
                        print("❌ 找到 failed 控件")
                        failed_found = True
                        return False
                except:
                    pass
            
            except Exception as e:
                print(f"⚠️ 检查刷写状态时出错: {e}")
            
            time.sleep(check_interval)
        
        # 检查结果
        if failed_found:
            print("❌ 刷写失败：检测到 failed")
            return False
        
        if not success_found:
            print(f"❌ 刷写超时：{max_wait_time} 秒内未检测到 success")
            return False
        
        # 找到 success 后，点击 EXIT 按钮退出窗口
        print("查找 EXIT 按钮...")
        exit_button = None
        max_retries = 10
        
        for i in range(max_retries):
            try:
                # 尝试查找 EXIT 按钮
                exit_titles = ["Exit", "EXIT"]
                for title in exit_titles:
                    try:
                        exit_button = flash_window.child_window(class_name="Button", title=title)
                        if exit_button.exists():
                            print(f"✅ 找到 EXIT 按钮: {title}")
                            break
                    except:
                        pass
                
                if exit_button and exit_button.exists():
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not exit_button or not exit_button.exists():
            print("⚠️ 无法找到 EXIT 按钮")
        else:
            print("点击 EXIT 按钮退出刷写窗口...")
            try:
                exit_button.click()
                time.sleep(1)
                print("✅ 已点击 EXIT 按钮")
                
                # 验证是否真的退出了刷写窗口
                print("验证刷写窗口是否已关闭...")
                try:
                    if not flash_window.exists() or not flash_window.is_visible():
                        print("✅ 刷写窗口已成功关闭")
                    else:
                        print("⚠️ 刷写窗口似乎仍存在")
                        # 再次尝试点击 EXIT
                        if exit_button.exists():
                            print("尝试再次点击 EXIT...")
                            exit_button.click()
                            time.sleep(1)
                except:
                    print("✅ 刷写窗口已关闭")
                    
            except Exception as e:
                print(f"⚠️ 点击 EXIT 按钮失败: {e}")
        
        print("✅ MCU文件刷写完成")
        return True

    except Exception as e:
        print(f"❌ 刷写操作过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False        

if __name__ == "__main__":
    main()