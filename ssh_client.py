import time
import re
import json
import paramiko
download_path = "/tmp/diff_pack_download"

class SshClient:
    def __init__(self, Architecture=None, password="#7F7d8or"):
        if Architecture is None:
            self.ssh_password = password
            print("debug here1")
        elif Architecture == 'ORINX':
            self.Architecture = Architecture
            self.ssh_password = "W8k3L2@m;"
            print("debug here3")
        elif Architecture == "ORINY":
            self.Architecture = Architecture
            self.ssh_password = "#7F7d8or"
            print("debug here4")
        elif Architecture == "THOR":
            self.Architecture = Architecture
            self.ssh_password = "G7#kL2@m"
            print("debug here5")
        else:
            print("[ERROR]:wrong architect!\n"
                  "pls select the architect below:\n"
                  "ORINX\ORINY\THOR\n")
            raise ValueError(f"unkonw architect: {Architecture}")

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_port = 22
        self.ssh_username = "nvidia"
    def ssh_connect(self, ip="172.16.2.14"):
        """建立 SSH 连接"""
        self.ssh_client.connect(
            hostname=ip,
            username=self.ssh_username,
            password=self.ssh_password,
            port=self.ssh_port,
            timeout=10
        )

    def execu_cmd(self, cmd: str):
        """执行 SSH 命令，返回 stdout/stderr"""
        recv_data = ""
        error_data = ""
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd, get_pty=True)

        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                recv_data += stdout.read(1024).decode('utf-8', errors='ignore')
            if stderr.channel.recv_ready():
                error_data += stderr.read(1024).decode('utf-8', errors='ignore')
        
        recv_data += stdout.read().decode('utf-8', errors='ignore')
        error_data += stderr.read().decode('utf-8', errors='ignore')

        if recv_data:
            print(f"stdout信息: {recv_data}")
        if error_data:
            print(f"stderr信息: {error_data}")
        return recv_data, error_data, stdin

    def ssh_close(self):
        """关闭 SSH 连接"""
        self.ssh_client.close()
        print("ssh close done")

    def extract_full_name(self):
        """提取 head ADS.METADATA"""
        pattern = r'"FullName":\s*"([^"]+)"'
        data_str = self.execu_cmd("head -n 21 /opt/deeproute/ADS.METADATA")[0]
        match = re.search(pattern, data_str)
        if match:
            print(match.group(1))
            return match.group(1)
        return ""

    def extract_soc_version(self):
        """提取 SOC 版本"""
        data_str = self.execu_cmd("cat /etc/version")[0]
        return data_str

    def extract_tail(self):
        """提取 tail ADS.METADATA"""
        pattern = r'"ShortName":\s*"([^"]+)"'
        data_str = self.execu_cmd("tail -n 25 /opt/deeproute/ADS.METADATA")[0]
        match = re.search(pattern, data_str)
        if match:
            short_name = match.group(1)
            print(f"提取的ShortName: {short_name}")
            return short_name
        return ""

    def extract_dr_info(self):
        """提取 dr_info.json 数据"""
        data_str = self.execu_cmd("cat /ota/source_package/dr_info.json")[0]
        return json.loads(data_str)

    def extract_gwm_version(self):
        """提取 GWM 版本文件内容"""
        data_str = self.execu_cmd("cat /opt/deeproute/driver/config/diagnostic/gwm*")[0]
        return data_str

    def dem_status(self):
        """获取 DEM 服务状态"""
        data = self.execu_cmd("systemctl status dem |head -11")[0]
        return data

    def dem_restart(self, password=None):
        """重启 DEM 服务"""
        if password is None:
            password = self.ssh_password
            print("pls enter password!!!using default password")
        
        stdin, stdout, stderr = self.ssh_client.exec_command(
            "sudo systemctl restart dem", get_pty=True, timeout=20
        )
        time.sleep(1)
        stdin.write(f"{password}\n")
        stdin.flush()
        print("entered password")

        for i in range(20, 0, -1):
            print(f"dem restart... be patient...cnt:{i}s  ", end='\r')
            time.sleep(1)
        print("\r\n")
        return self.dem_status()

    def test(self):
        """统一提取所有 SSH 相关信息"""
        soc_info = {}
        self.ssh_connect()
        
        # 提取各字段
        soc_info["head-ADS.METADATA"] = self.extract_full_name()
        soc_info["tail-ADS.METADATA"] = self.extract_tail()
        soc_info["SOC_version"] = self.extract_soc_version()
        soc_info["file_gwm_version"] = self.extract_gwm_version()
        soc_info["dem_status"] = self.dem_status()
        soc_info["dr_info"] = self.extract_dr_info()
        soc_info["dem_restart"] = self.dem_restart()
        
        self.ssh_close()
        return soc_info
    
    def after_test(self):
        soc_info = {}
        self.ssh_connect()
        soc_info["dr_info"] = self.extract_dr_info()
        soc_info["dem_status"] = self.dem_status()
        soc_info["file_gwm_version"] = self.extract_gwm_version()
        self.ssh_close()
        return soc_info