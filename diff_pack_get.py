import requests
import os
import sys
import time
import hashlib
import shutil
import subprocess
import feishu
from my_serial import Serial_device
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer adas-farm_77868_+ae2dmmu48degsjfayynp2n9o5ca3bbr"
DOWNLOAD_PATH = "/tmp/diff_pack_download"

class DiffPackClient:
    def __init__(self,Architecture=None,workflow_id=None):
        self.architecture = Architecture.upper() if Architecture else "NONE"
        self.switch_en = False
        if self.architecture is None:
            self.ssh_password = "#7F7d8or"
        elif self.architecture == 'ORINX':
            self.ssh_password = "W8k3L2@m;"
        elif self.architecture == "ORINY":
            self.ssh_password = "#7F7d8or"
        elif self.architecture == "THOR":
            self.ssh_password = "G7#kL2@m"
            self.switch_en = True
        else:
            print("[ERROR]:wrong architect!\n"
                  "pls select the architect below:\n"
                  "ORINX\ORINY\THOR\n")
            raise ValueError(f"unkonw architect: {Architecture}")
        self.download_path = DOWNLOAD_PATH
        self.workflow_id = workflow_id
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def get_diffpack_url(self):
        diffpack_id = self.get_diffpack_id()
        if diffpack_id:
            headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            resp = requests.get(f"{API_BASE_URL}/api/v1/workflow/diff-tasks/{diffpack_id}", headers=headers, verify=False, data=None)
            resp.raise_for_status()
            raw_data = resp.json().get('data', {})
            # print(f"原始 API 响应数据: {raw_data}") 

            return raw_data.get('downloadUrl')
        return None

    def get_diffpack_id(self):
        headers  = headers = {
            'Authorization': API_TOKEN,
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        workflow_data = resp.json().get('data', {})
        diff_status = workflow_data.get('diffMsg')
        if(diff_status is not None):
            diffpack_id = workflow_data.get('diffId')
            print(f"diffpack_id: {diffpack_id}")
            return  f"{diffpack_id}"
        print(f"diff状态: {diff_status}")
        return None
    def download_diffpack(self, url):
        if url is None:
            print("No diffpack URL found.")
            raise ValueError("No diffpack URL found.")
        os.system(f"wget -O {self.download_path}/a.zip '{url}' --no-check-certificate")

    def scp_diffpack(self):
        # os.system(f"sshpass -p '{self.ssh_password}' scp {self.download_path}/a.zip nvidia@172.16.2.14:/data/a.zip")
        os.system(f"sshpass -p '{self.ssh_password}' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.download_path}/a.zip nvidia@172.16.2.14:/data/a.zip")
    def get_injectpack_uuid(self):
        # Implementation for getting injectpack UUID
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        uuid = resp.json().get('data').get("uuid")
        print(f"原始 API 响应数据: {uuid}")
        return uuid
    def get_injectpack_package_url(self):
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v1/artifacts/{self.get_injectpack_uuid()}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        url = resp.json().get('downloadUrl')
        print(f"原始 API 响应数据: {url}")
        return url
    def get_pack_release_soc_md5(self):
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v1/artifacts/{self.get_injectpack_uuid()}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        md5 = resp.json().get('sourceSoc').get('md5Sum')
        print(f"原始 API 响应数据: {md5}")
        return md5
    def download_and_extract_injectpack(self, extract_path="/tmp/flash_content"):
        url = self.get_injectpack_package_url()
        if url is None:
            raise ValueError("No injectpack URL found.")

        # Step 1: 下载并解压灌装包到临时目录
        tmp_dir = os.path.join(self.download_path, "injectpack_tmp")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        zip_path = os.path.join(tmp_dir, "injectpack.zip")

        ret = os.system(f"wget -O '{zip_path}' '{url}' --no-check-certificate")
        if ret != 0:
            raise RuntimeError(f"wget failed with code {ret}")

        ret = os.system(f"unzip -o '{zip_path}' -d '{tmp_dir}'")
        if ret != 0:
            shutil.rmtree(tmp_dir)
            raise RuntimeError(f"unzip main package failed with code {ret}")
        os.remove(zip_path)

        # Step 2: 查找含 SOC 关键字的 zip 包
        flash_package_dir = os.path.join(tmp_dir, "flash_package")
        soc_zips = [
            f for f in os.listdir(flash_package_dir)
            if "SOC" in f and f.endswith(".zip")
        ]
        if not soc_zips:
            shutil.rmtree(tmp_dir)
            raise FileNotFoundError(f"No SOC zip found in {flash_package_dir}")
        if len(soc_zips) > 1:
            print(f"[WARNING] Multiple SOC zips found, using first: {soc_zips}")
        soc_zip_path = os.path.join(flash_package_dir, soc_zips[0])

        # Step 3: MD5 校验
        expected_md5 = self.get_pack_release_soc_md5()
        md5 = hashlib.md5()
        with open(soc_zip_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        actual_md5 = md5.hexdigest()
        print(f"Expected MD5: {expected_md5}")
        print(f"Actual   MD5: {actual_md5}")
        if actual_md5 != expected_md5:
            shutil.rmtree(tmp_dir)
            raise ValueError(f"MD5 mismatch: expected {expected_md5}, got {actual_md5}")
        print("MD5 verification passed.")

        # Step 4: 清空目标目录，把 SOC 包解压进去
        # 用 sudo 处理目标目录：可能由上次 sudo 操作创建，普通用户无法删除
        os.system(f"sudo rm -rf '{extract_path}'")
        os.system(f"sudo mkdir -p '{extract_path}'")
        ret = os.system(f"sudo unzip -o '{soc_zip_path}' -d '{extract_path}'")
        if ret != 0:
            raise RuntimeError(f"unzip SOC package failed with code {ret}")
        print(f"SOC package extracted to {extract_path}")

        # Step 5: 删除临时目录（其他所有内容）
        shutil.rmtree(tmp_dir)
        print("Cleanup done.")

    def flash_soc(self, extract_path="/tmp/flash_content", serial_port="/dev/ttyUSB0",
                  nvidia_wait_timeout=60):
        # Step 1: 串口发送指令，让 SOC 进入 recovery 模式
        ser = Serial_device(port=serial_port)
        try:
            if not ser.open():
                raise RuntimeError(f"Failed to open serial port {serial_port}")

            print("[FLASH] Sending poweron...")
            ser.send_data("poweron\r\n")

            print("[FLASH] Waiting 10s...")
            time.sleep(10)

            print("[FLASH] Sending tegrarecovery x1 on...")
            ser.send_data("tegrarecovery x1 on\r\n")

            print("[FLASH] Waiting 5s...")
            time.sleep(5)

            print("[FLASH] Sending tegrareset x1...")
            ser.send_data("tegrareset x1\r\n")
        finally:
            ser.close()

        # Step 2: 轮询 lsusb，等待 NVIDIA 设备枚举（recovery 模式下会出现）
        print(f"[FLASH] Waiting for NVIDIA USB device (timeout={nvidia_wait_timeout}s)...")
        deadline = time.time() + nvidia_wait_timeout
        nvidia_found = False
        while time.time() < deadline:
            result = subprocess.run(["lsusb"], capture_output=True, text=True)
            if "NVIDIA" in result.stdout:
                print("[FLASH] NVIDIA device detected on USB.")
                nvidia_found = True
                break
            time.sleep(2)

        if not nvidia_found:
            raise RuntimeError(
                f"NVIDIA device not found on USB after {nvidia_wait_timeout}s. "
                "Check recovery mode or USB connection."
            )

        # Step 3: 定位并执行 flash.sh
        flash_sh = os.path.join(extract_path, "flash.sh")
        if not os.path.exists(flash_sh):
            raise FileNotFoundError(f"flash.sh not found in {extract_path}")

        print(f"[FLASH] Running flash.sh in {extract_path} ...")
        ret = os.system(f"cd '{extract_path}' && sudo bash flash.sh")
        if ret != 0:
            raise RuntimeError(f"flash.sh exited with code {ret}")
        print("[FLASH] SOC flash complete.")

    def get_guanzhuang_pack_info(self):
        # Implementation for getting injectpack info
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        filter_driver = {"fullName":"sourceDriver",
                         "gwmShortName":"sourceDriver",
                         "packageName":"sourceDsvSoc",            
                         }
        filter_mcu = {
                            "uuid":"sourceMcu",
                            "packageName":"sourceMcu",  
        }
        filter_switch = {
                            "uuid":"sourceSwitch",
                            "packageName":"sourceSwitch",   
        }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        raw_data = resp.json().get('data').get("sourceFOTA")
        # print(f"原始 API 响应数据: {raw_data}")
        ret = {
            "mcu":{
                "uuid":raw_data.get("sourceMcu",{}).get("uuid"),
                "packageName":f"{raw_data.get('sourceMcu',{}).get('packageName')}={raw_data.get('sourceMcu',{}).get('version')}",
                "version":raw_data.get("sourceMcu",{}).get("oemVersion"),
                "md5":raw_data.get("sourceMcu",{}).get("md5Sum"),
            },
            "switch":{
                "uuid":raw_data.get("sourceSwitch",{}).get("uuid"),
                "packageName":f"{raw_data.get('sourceSwitch',{}).get('packageName')}={raw_data.get('sourceSwitch',{}).get('version')}",
                "version":raw_data.get("sourceSwitch",{}).get("oemVersion"),
                "md5":raw_data.get("sourceSwitch",{}).get("md5Sum"),
            },
            "driver":{
                "fullName":raw_data.get("sourceDriver",{}).get("fullName"),
                "gwmShortName":raw_data.get("sourceDriver",{}).get("gwmShortName"),
                "socVersion":raw_data.get("sourceSoc").get("sourceDsvSoc",{}).get("packageName"),
                "oemVersion":raw_data.get("sourceDriver",{}).get("oemVersion"),
            }
            }
        if self.switch_en:
            ret["switchb"] = {
                "uuid": raw_data.get("sourceSwitchB", {}).get("uuid"),
                "packageName":f"{raw_data.get('sourceSwitchB',{}).get('packageName')}={raw_data.get('sourceSwitchB',{}).get('version')}",
                "version": raw_data.get("sourceSwitchB", {}).get("oemVersion"),
                "md5": raw_data.get("sourceSwitchB", {}).get("md5Sum"),
            }
        # print(f"injectpack info: {ret}")
        return ret

    def get_cam_version(self):
        # Implementation for getting cam version
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        version = resp.json().get('data').get("camFullName",{})
        # print(f"原始 API 响应数据: {version}")
        return version
    def get_gnss_version(self):
        # Implementation for getting gnss version
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        tmp_data = resp.json().get('data').get("sourceFOTA",{}).get('sourceSupplierArtifacts')
        version  = tmp_data[0].get('version')
        pre_str = tmp_data[0].get('packageName')
        # print(f"原始 API 响应数据: {version, pre_str}")
        return f"{pre_str}={version}"
    def get_gwm_version(self):
        ret = self.get_guanzhuang_pack_info()
        return ret.get("driver",{}).get("oemVersion")
    def get_all_versions_summary(self):
        """
        获取所有版本信息汇总
        :return: dict, 格式如下
            {
                "injectpack": {...},   # get_guanzhuang_pack_info 返回的字典
                "cam_version": "...",  # get_cam_version 返回的字典或字符串
                "gnss_version": "packageName=version"  # get_gnss_version 返回的字符串
            }
        """
        summary = {}

        # 1. 获取 injectpack 信息
        try:
            injectpack_info = self.get_guanzhuang_pack_info()
            summary['injectpack'] = injectpack_info
        except Exception as e:
            print(f"获取 injectpack 信息失败: {e}")
            summary['injectpack'] = {}

        # 2. 获取 CAM 版本信息
        try:
            cam_version = self.get_cam_version()
            summary['cam_version'] = cam_version
        except Exception as e:
            print(f"获取 CAM 版本信息失败: {e}")
            summary['cam_version'] = {}

        # 3. 获取 GNSS 版本信息
        try:
            gnss_version = self.get_gnss_version()
            summary['gnss_version'] = gnss_version
        except Exception as e:
            print(f"获取 GNSS 版本信息失败: {e}")
            summary['gnss_version'] = ""

        return summary
    def extract_key_versions(self):
        """
        从完整的 injectpack 数据中提取关键版本信息
        """
        data = self.get_all_versions_summary()
        injectpack = data.get('injectpack', {})
        if self.switch_en:
            return{
                "mcu_version": injectpack.get('mcu', {}).get('version'),
                "mcu_md5": injectpack.get('mcu', {}).get('md5'),
                "switch_version": injectpack.get('switch', {}).get('version'),
                "switch_md5": injectpack.get('switch', {}).get('md5'),
                "switchb_version": injectpack.get('switchb', {}).get('version'),
                "switchb_md5": injectpack.get('switchb', {}).get('md5'),
                "soc_version": injectpack.get('driver', {}).get('socVersion'),
                "gwm_version": injectpack.get('driver', {}).get('oemVersion'),
                "driver_fullName": injectpack.get('driver', {}).get('fullName'),
                "driver_gwmShortName": injectpack.get('driver', {}).get('gwmShortName'),
                "dr_info":str({
                    'mcu_version': injectpack.get('mcu', {}).get('packageName'),
                    'switch_5192a_version': injectpack.get('switch', {}).get('packageName'),
                    'switch_5192b_version': injectpack.get('switchb', {}).get('packageName'),
                    'soc_version': injectpack.get('driver', {}).get('socVersion'),
                    'cam_version': data.get('cam_version'),
                    'gnss_version': data.get('gnss_version'),
                    'package_version':"",
                    'gwm_version': injectpack.get('driver', {}).get('oemVersion'),
                    'driver_verison':injectpack.get('driver', {}).get('fullName'),
                }),
                "cam_version": data.get('cam_version'),
                "gnss_version": data.get('gnss_version')
                
            }
        else:
            return {
                "mcu_version": injectpack.get('mcu', {}).get('version'),
                "mcu_md5": injectpack.get('mcu', {}).get('md5'),
                "switch_version": injectpack.get('switch', {}).get('version'),
                "switch_md5": injectpack.get('switch', {}).get('md5'),
                "soc_version": injectpack.get('driver', {}).get('socVersion'),
                "gwm_version": injectpack.get('driver', {}).get('oemVersion'),
                "driver_fullName": injectpack.get('driver', {}).get('fullName'),
                "driver_gwmShortName": injectpack.get('driver', {}).get('gwmShortName'),
                "dr_info":str({
                    'mcu_version': injectpack.get('mcu', {}).get('packageName'),
                    'switch_version': injectpack.get('switch', {}).get('packageName'),
                    'soc_version': injectpack.get('driver', {}).get('socVersion'),
                    'cam_version': data.get('cam_version'),
                    'gnss_version': data.get('gnss_version'),
                    'package_version':"",
                    'gwm_version': injectpack.get('driver', {}).get('oemVersion'),
                    'driver_verison':injectpack.get('driver', {}).get('fullName'),
                }),
                "cam_version": data.get('cam_version'),
                "gnss_version": data.get('gnss_version')
            }
    


def test():
    client = DiffPackClient(Architecture="THOR", workflow_id="86ebf5be-f311-4a2f-9df2-dbc0617cffc4")
    repo = feishu.FeishuReporter("thor")
    repo.create_guanzhuang_template("008")
    repo.update_expect_result(client.extract_key_versions())
    # client.get_guanzhuang_pack_info()
    # client.get_gnss_version()
    # client.get_cam_version()
    # print(f"所有版本信息汇总: {client.extract_key_versions()}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python diff_pack_get.py <architecture> <workflowId> [serialPort]")
        print("  architecture : ORINX | ORINY | THOR")
        print("  workflowId   : workflow UUID")
        print("  serialPort   : serial device path (default: /dev/ttyUSB0)")
        sys.exit(1)

    architecture = sys.argv[1]
    workflow_id  = sys.argv[2]
    serial_port  = sys.argv[3] if len(sys.argv) >= 4 else "/dev/ttyUSB0"

    client = DiffPackClient(Architecture=architecture, workflow_id=workflow_id)

    print("=" * 60)
    print("[STEP 1] 下载并解压 SOC 刷写包，验证 MD5")
    print("=" * 60)
    client.download_and_extract_injectpack()

    print("=" * 60)
    print(f"[STEP 2] 开始刷写 SOC（串口: {serial_port}）")
    print("=" * 60)
    client.flash_soc(serial_port=serial_port)

    print("=" * 60)
    print("[DONE] SOC 刷写完成")
    print("=" * 60)
