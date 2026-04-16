import sys
import subprocess
import os
import re
import time
import json
import inject_key
from ssh_client import SshClient
from doip import DoipClient
from my_serial import Serial_device
from feishu import FeishuRobot,FeishuReporter
from diff_pack_get import DiffPackClient

soc_flash_en = False

class Prework():
    def __init__(self,net:str='enx207bd51a13cc'):
        self.net = net
        pass
    def execute(self,command:str):
        try:
            ret = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=10  # 添加超时
            )
            
            # 检查返回码
            if ret.returncode == 0:
                return ret.stdout  # 修复拼写错误
            else:
                # 返回错误信息，同时包含 stdout 和 stderr
                error_msg = f"命令执行失败 (返回码: {ret.returncode})\n"
                if ret.stderr:
                    error_msg += f"错误: {ret.stderr}\n"
                if ret.stdout:
                    error_msg += f"输出: {ret.stdout}"
                return error_msg
                
        except subprocess.TimeoutExpired:
            return "错误: 命令执行超时"
        except Exception as e:
            return f"错误: {e}"    
    def doip_net_setup(self):
        self.execute(f"sudo ip link add link {self.net} name mgbe3_0.2 type vlan id 2 >/dev/null 2>&1 || true")
        self.execute(f"sudo ip link set mgbe3_0.2 type vlan egress 0:2 1:2 2:2 3:2 4:2 5:2 6:2 7:2")
        self.execute(f"sudo ip address add 172.16.2.58/24 dev mgbe3_0.2 >/dev/null 2>&1 || true")
        # self.execute(f"sudo ip link set dev mgbe3_0.2 address 02:47:57:4d:00:58")
        self.execute(f"sudo ip link set dev mgbe3_0.2 up")
        print("network setting complete...")
    def key_inject_net_setup(self):
        self.execute(f"sudo ip link add link {self.net} name mgbe3_0.5 type vlan id 5 >/dev/null 2>&1 || true")
        self.execute(f"sudo ip link set mgbe3_0.5 type vlan egress 0:2 1:2 2:2 3:2 4:2 5:2 6:2 7:2")
        self.execute(f"sudo ip address add 172.16.5.58/24 dev mgbe3_0.5 >/dev/null 2>&1 || true")
        # self.execute(f"sudo ip link set dev mgbe3_0.5 address 02:47:57:4d:00:58")
        self.execute(f"sudo ip link set dev mgbe3_0.5 up")
        print("network setting complete...")
    def network_prepare(self):
        self.execute(f"sudo ip link set dev {self.net} address 02:47:57:4d:00:58")
        self.doip_net_setup()
        self.key_inject_net_setup()
    def clean_space(self):
        self.execute("sudo rm -rf /tmp/flash_content/*")
        self.execute("sudo rm -rf /tmp/diff_pack_download/*")
    def space_check(self):
        ret = self.execute("df -h / | awk 'NR==2 {print $4}'")
        avail_space = ret.strip()
        if 'G' or 'M' or 'K' in avail_space:
            if 'G' in avail_space:
                data = int(avail_space.replace("G",""))
                if data <= 100:
                    print(f"space left {data}GB,need 100GB")
                else:
                    return 0
            elif 'M' in avail_space:
                data = int(avail_space.replace("M",""))
                print(f"space left {data}MB,need 100GB")
                return -1 
            elif 'K' in avail_space:
                data = int(avail_space.replace("K",""))
                print(f"space left {data}KB,need 100GB")
                return -1 
        elif avail_space == '0':
            print(f"space left 0,need 100GB")
            return -1 
        return -1


    


def serial_check():
    mcu_serial = None
    try:
        mcu_serial = Serial_device()  # ttyUSB0
        mcu_serial.send_data("aurixreset\r\n") 
        time.sleep(10)  # 等待MCU重启完成
        mcu_serial.send_data("poweron\r\n")  # just in case
        time.sleep(10)
        
        # 获取 MCU 版本
        mcu_version = mcu_serial.get_version(cmd='version\r\n', max_retries=5, retry_delay=1)
        if mcu_version is None:
            print("[WARNING]: could not find mcu version")
        
        # 获取 Switch 版本
        switch_version = mcu_serial.get_version(cmd='switch\r\n', max_retries=5, retry_delay=1)
        if switch_version is None:
            print("[WARNING]: could not find switch version")
            # 返回 (mcu_version, (None, None))
            return mcu_version, (None, None)
        
        # 确保 switch_version 是元组格式
        if isinstance(switch_version, str):
            # 如果是字符串，转换为元组
            switch_version = (switch_version, None)
        elif not isinstance(switch_version, tuple):
            # 其他类型，设为 None
            switch_version = (None, None)
        
        return mcu_version, switch_version
        
    except FileNotFoundError as e:
        error_msg = f"could not find ttyUSB0: {e}"
        print(f"[ERROR] {error_msg}")
        return None, (None, None)
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"[ERROR] {error_msg}")
        return None, (None, None)
        
    finally:
        if mcu_serial and hasattr(mcu_serial, 'close'):
            mcu_serial.close()


def ssh_check(car_type='ORINX',car_t='C01'):
    ssh_test = SshClient(Architecture=car_type.upper(),password='',car_type=car_t)
    test_info = ssh_test.test()
    return test_info

def inject_key_check(car_type = 'C01',Architecture = 'ORINX'):
    if Architecture == 'ORINX':
        return None
    else:
        inject_key.set_network("enx207bd51a13cc")
        import subprocess
        import sys
        
        def ping_host(ip, timeout=3, retry_count=5):
            """
            检测指定IP是否可达
            :param ip: 目标IP地址
            :param timeout: 单次ping超时时间(秒)
            :param retry_count: 重试次数
            :return: 可达返回True，否则返回False
            """
            # 根据操作系统选择ping参数
            param = '-n' if sys.platform.lower().startswith('win') else '-c'
            param_timeout = '-w' if sys.platform.lower().startswith('win') else '-W'
            
            for i in range(retry_count):
                try:
                    # 执行ping命令
                    cmd = ['ping', param, '1', param_timeout, str(timeout), ip]
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout+1)
                    
                    if result.returncode == 0:
                        print(f"\n✓ 网络连通性检测成功: {ip} 可达 (尝试次数: {i+1})")
                        return True
                    else:
                        print(f"  网络检测中... {ip} 不可达，正在重试 ({i+1}/{retry_count})")
                        time.sleep(1)
                except subprocess.TimeoutExpired:
                    print(f"  网络检测超时... {ip} 无响应，正在重试 ({i+1}/{retry_count})")
                    time.sleep(1)
            
            print(f"\n✗ 网络连通性检测失败: {ip} 不可达，请检查网络连接")
            return False
        
        # 执行网络检测
        target_ip = "172.16.5.14"
        print(f"正在检测网络连通性，目标IP: {target_ip}")
        
        if not ping_host(target_ip):
            # 网络不通，可以选择退出或抛出异常
            raise Exception(f"无法连接到目标设备 {target_ip}，请检查网卡配置和网络连接")
        
        # 网络连通，继续执行后续操作
        inject_key.inject_default_key()
        doip_test = DoipClient()
        doip_test.client_setup()
        doip_test.route_active()
        doip_test.hard_reset()
        doip_test.sock_close()
        for i in range(40,0,-1):
            print(f"ADCU start cnt:{i}s  ",end='\r')
            time.sleep(1)

        return 1
    
def doip_check(car_type = 'C01'):
    doip_test = DoipClient()
    doip_test.set_network("enx207bd51a13cc")
    doip_test.car_type = car_type
    doip_test.client_setup()
    doip_test.route_active()
    doip_test.write_F1B1_car_config_VIN()
    doip_test.hard_reset()
    doip_test.sock_close()
    for i in range(100,0,-1):
        print(f"ADCU start cnt:{i}s  ",end='\r')
        time.sleep(1)
    doip_test.client_setup()
    doip_test.route_active()
    doip_version = doip_test.check_guanzhuang_version()
    doip_test.sock_close()
    return doip_version
    
def doip_OTA(Architecture = 'ORINX'):
    doip_test = DoipClient()
    doip_test.client_setup()
    doip_test.route_active()
    ret = None
    if Architecture in ('ORINX','ORINY'):
        ret = doip_test.ORIN_ota_a_zip()


    elif Architecture == 'THOR':
        ret = doip_test.THOR_ota_a_zip()

    else:
        print("wrong archi!!!")
        ret = -1
    if ret ==0:
        return 'success OTA'
    elif ret == -1 :
        return 'not start OTA.wrong archi!!!'
    else:
        return "OTA failed,plz check the reason manually!!!"

def AFTER_OTA_CHECK(car_type='ORINX',car_t='C01'):
    ssh_test = SshClient(Architecture=car_type,password='',car_type=car_t)
    test_info = ssh_test.after_test()
    return test_info



if __name__ =='__main__':
    print("first para is architect ,second is car_type")
    if len(sys.argv)>3:
        car_TEST = sys.argv[1].upper()  #orin平台
        car_type = sys.argv[2]  #具体车型
        flow_id  = sys.argv[3] #灌装包工作流id
    else:
        car_TEST = 'ORINX'
        car_type = 'C01'
        flow_id = None
        raise Exception("pls input correct para!!!")
    feishu_test = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/86f13735-aa8e-4dc1-aa6a-258177111a1e")
    report =FeishuReporter(car_type)
    clean = Prework()
    clean.network_prepare()
    if(clean.space_check()!=0):
        clean.clean_space()
        if(clean.space_check()!=0):
            print("/tmp space need 100GB,pls check it.")
            feishu_test.send_text("/tmp space need 100GB,pls check it.")
            sys.exit(-1)
    diff_client = DiffPackClient(Architecture=car_TEST, workflow_id=flow_id)
    inject_pack_uuid = diff_client.get_injectpack_uuid()
    if(soc_flash_en):
        print("[DEBUG]start to flash SOC")

        print("=" * 60)
        print("[STEP 1] 下载并解压 SOC 刷写包，验证 MD5")
        print("=" * 60)
        diff_client.download_and_extract_injectpack()

        print("=" * 60)
        print(f"[STEP 2] 开始刷写 MCU serial: /dev/ttyUSB0, inject pack uuid: {inject_pack_uuid}")
        print("=" * 60)
        diff_client.flash_soc()

        print("=" * 60)
        print("[DONE] SOC 刷写完成")
        print("=" * 60)

    mcu_version,switch_version = serial_check()
    try:
        result = inject_key_check(car_type='C01', Architecture='other')
        
        if result is None:
            print("架构为 ORINX，无需执行注入操作")
        elif result == 1:
            print("✓ 密钥注入成功完成")
            feishu_test.send_text("✓ 密钥注入成功完成")
            # 在这里执行成功后的业务逻辑
            
    except Exception as e:
        print(f"✗ 密钥注入失败: {e}")    
        feishu_test.send_text(f"✗ 密钥注入失败: {e}")
        sys.exit(-1)
    # inject_key_check(car_type=car_type,Architecture=car_TEST)

    doip_guangzhuang_version = doip_check(car_type) ##配置字刷写完有几率无法connect
    test_info = ssh_check(car_TEST,car_type)
    report.create_guanzhuang_template(diff_client.get_gwm_version(), workflow_id=flow_id)
    report.update_expect_result(diff_client.extract_key_versions())
    test_result = {
            "mcu_md5": None,
            "switch_md5": None,
            "switchb_md5": None,
            "mcu_version": mcu_version,
            "switch_version":switch_version[0],
            "switchb_version": switch_version[1],
            "soc_version": test_info["soc_version"],
            "dem_status":test_info["dem_status"],
            "dem_restart":test_info["dem_restart"],
            "driver_fullName":test_info["driver_fullName"],
            "driver_gwmShortName":test_info["driver_gwmShortName"],
            "gwm_version":str(test_info["gwm_version"]),
            "dr_info":str(test_info["dr_info"]),
            "doip_gwm_version":doip_guangzhuang_version["gwm_version"],
            "doip_gwm_software_infomation":doip_guangzhuang_version["gwm_software_infomation"],
            "doip_gwm_calibration_version":doip_guangzhuang_version["gwm_Calibration_version"],
            "ota_result":None,
            "ota_gwm_version":None,
            "ota_dem_status":None,
            "ota_dr_info":None

    }
    report.update_test_result(test_result)
#     feishu_test.send_text(
#     content=f"--------------------- can inject test ---------------------\r\n\
# \r\n\
# --------------------- 1. serial read - MCU ---------------------\r\n\
# {mcu_version}  \r\n\
# \r\n\
# --------------------- 2. serial read - switch ---------------------\r\n\
# {switch_version} \r\n\
# \r\n\
# --------------------- 3. head ADS-METADATA ---------------------\r\n\
# {test_info['head-ADS.METADATA']}\r\n\
# \r\n\
# --------------------- 4. tail ADS-METADATA ---------------------\r\n\
# {test_info['tail-ADS.METADATA']}\r\n\
# \r\n\
# --------------------- 5. SOC version ---------------------\r\n\
# {test_info['SOC_version']} \r\n\
# \r\n\
# --------------------- 6. file_gwm_version ---------------------\r\n\
# GWM 版本：{test_info['file_gwm_version']}\r\n\
# --------------------- 7. DEM status ---------------------\r\n\
# {test_info['dem_status']}  \r\n\
# \r\n\
# --------------------- 8. read dr_info ---------------------\r\n\
# {test_info['dr_info']}\r\n\
# \r\n\
# --------------------- 9.DOIP read version ---------------------\r\n\
#  gwm_version:{doip_guangzhuang_version['gwm_version']}\r\n\
#  gwm_software_infomation:{doip_guangzhuang_version['gwm_software_infomation']}\r\n\
#  gwm_Calibration_version:{doip_guangzhuang_version['gwm_Calibration_version']}\r\n\
# # --------------------- 10. DEM restart status ---------------------\r\n\
# {test_info['dem_restart']} \r\n\
# \r\n\
# start to ota test..."
# )
    for i in range(60,0,-1):
        print(f"dem init cnt:{i}s  ",end='\r')
        time.sleep(1)
    diff_url = diff_client.get_diffpack_url()
    if diff_url is None:
        print("diff_pack url is none")
        feishu_test.send_text("no diff pack...")
        sys.exit(-1)
    diff_client.download_diffpack(diff_url)
    diff_client.scp_diffpack()

    ret = doip_OTA(car_TEST)
    if ret == 'success OTA':
        feishu_test.send_text(ret)
        ret = AFTER_OTA_CHECK(car_TEST)
        test_result["ota_result"] = "success"
        test_result["ota_dem_status"] =ret["dem_status"]
        test_result["ota_dr_info"] =ret["dr_info"]
        test_result["ota_gwm_version"] = ret["file_gwm_version"]
#         feishu_test.send_text(f"--------------------- 1. file_gwm_version ---------------------\r\n\
# GWM 版本：{ret['file_gwm_version']}\r\n\
# --------------------- 2. DEM status ---------------------\r\n\
# {ret['dem_status']}  \r\n\
# \r\n\
# --------------------- 3. read dr_info ---------------------\r\n\
# {ret['dr_info']}\r\n\
# \r\n:")
    elif ret == 'not start OTA.wrong archi!!!':
        feishu_test.send_text(ret)
    else:
        feishu_test.send_text(ret)
        test_result["ota_result"] = "FAIL"
    
    report.update_test_result(test_result)


    ...
