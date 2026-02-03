import os
import sys
import glob
import shutil
from common.config import CAR_CONFIG, SOC_SERAL_PORT
from common.utils import clean_old_firmware, get_download_url, download_file, extract_zip_file

def _clean_extracted_folders(directory):
    """清理解压后的文件夹（保留 ZIP 文件）"""
    if not os.path.exists(directory):
        return
    
    print(f"[清理] 正在清理解压后的文件夹: {directory}")
    deleted_count = 0
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        # 跳过 ZIP 文件
        if item.lower().endswith('.zip'):
            continue
        
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"  - 已删除文件夹: {item}")
                deleted_count += 1
        except Exception as e:
            print(f"  - 删除失败 {item}: {e}")
    
    if deleted_count > 0:
        print(f"[清理] 完成: 已清理 {deleted_count} 个文件夹")

def _find_extracted_folder(directory, zip_file):
    """查找解压后的文件夹（通常是 ZIP 文件名去掉扩展名）"""
    zip_basename = os.path.basename(zip_file)
    zip_name_without_ext = os.path.splitext(zip_basename)[0]
    
    # 可能的文件夹名称
    possible_names = [
        zip_name_without_ext,
        zip_basename.replace('.zip', ''),
    ]
    
    for name in possible_names:
        folder_path = os.path.join(directory, name)
        if os.path.isdir(folder_path):
            return name
    
    # 如果没找到，返回目录中唯一的文件夹（如果有）
    folders = [f for f in os.listdir(directory) 
               if os.path.isdir(os.path.join(directory, f)) and not f.lower().endswith('.zip')]
    
    if len(folders) == 1:
        return folders[0]
    
    return None

def main():
    print("=== SOC 固件下载脚本 ===\n")
    
    # 1. 解析命令行参数
    if len(sys.argv) < 3:
        print("❌ 错误: 参数不足")
        print("用法: python flash_soc.py <车型> <SOC_UUID>")
        print("示例: python flash_soc.py Thor 3efe73e3-6c37-4084-9adc-d0c10b7f975b")
        sys.exit(1)
        
    car_input = sys.argv[1].strip()
    input_uuid = sys.argv[2].strip()
    
    # 确定车型
    if car_input.lower() == "p03":
        car_model = "P03"
    elif car_input.lower() == "thor":
        car_model = "Thor"
    elif car_input.lower() == "c01":
        car_model = "C01"
    else:
        print(f"❌ 错误: 不支持的车型 '{car_input}'")
        print("支持的车型列表: P03, Thor, C01")
        sys.exit(1)

    # 确定下载目录（使用 SOC 专用目录）
    config = CAR_CONFIG[car_model]
    target_soc_dir = config["soc_dir"]

    print(f"[配置] 目标 UUID: {input_uuid}")
    print(f"[配置] 车型: {car_model}")
    print(f"[配置] 下载目录: {target_soc_dir}\n")
    
    # 2. 清理旧 ZIP 文件和解压后的文件夹（下载前清理）
    clean_old_firmware(target_soc_dir, file_ext=".zip")
    # 清理解压后的文件夹（为后续解压做准备）
    _clean_extracted_folders(target_soc_dir)
    
    # 3. 获取 SOC 下载链接 (使用 /api/v1/artifacts/socs 路径)
    soc_download_url = get_download_url(input_uuid, car_model, artifact_type="socs")
    
    # 4. 执行下载
    if soc_download_url:
        downloaded_file = download_file(soc_download_url, target_soc_dir)
        if downloaded_file:
            print(f"\n✅ SOC 固件下载成功: {os.path.basename(downloaded_file)}")
            
            # 5. 解压 ZIP 文件到当前文件夹
            if downloaded_file.lower().endswith('.zip'):
                print(f"\n[解压] 开始解压 ZIP 文件...")
                if extract_zip_file(downloaded_file, extract_to=target_soc_dir):
                    print(f"✅ SOC 固件解压成功")
                    
                    # 6. 查找解压后的文件夹并 cd 进入（为后续刷写做准备）
                    extracted_folder = _find_extracted_folder(target_soc_dir, downloaded_file)
                    if extracted_folder:
                        extracted_path = os.path.join(target_soc_dir, extracted_folder)
                        print(f"[提示] 解压后的文件夹: {extracted_folder}")
                        print(f"[提示] 后续刷写需要进入: cd {extracted_path}")
                    else:
                        print(f"[提示] 解压后的文件在: {target_soc_dir}")
                else:
                    print("❌ 解压失败")
                    sys.exit(1)
            else:
                print("⚠️ 警告: 下载的文件不是 ZIP 格式")
        else:
            print("❌ 下载失败")
            sys.exit(1)
    else:
        print("❌ 错误: 无法获取 SOC 固件下载链接，流程终止。")
        sys.exit(1)

if __name__ == "__main__":
    main()

