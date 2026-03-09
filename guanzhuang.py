#!/usr/bin/env python3
import paramiko
import time
import logging
import requests,json
import serial
import re
import socket
import logging
import sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import cmac

# App_ID = "cli_a72719d632be901c"
# App_Secret = "MWxgknshTRR5pIAgXDdDmhRwmIQdMdbN"


class Ssh_client():
    def __init__(self,car_type=None,password="#7F7d8or"):
        if car_type ==None:
            self.ssh_password = password
            print("debug here1")
        elif car_type == "C01" or car_type=='M8':
            self.car_type = car_type
            self.ssh_password = "W8k3L2@m;"
            print("debug here3")
        elif car_type == "P03":
            self.car_type = car_type
            self.ssh_password = "#7F7d8or"
            print("debug here4")
        elif car_type == 'DE09' or car_type =="C01-T":
            self.car_type = car_type
            self.ssh_password = "G7#kL2@m"
            print("debug here5")
        else:
            print("[ERROR]:wrong car type!\n"
                  "pls select the car type below:\n"
                  "C01\n"
                  "P03\n"
                  "DE09\n")
            return 0
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_port = 22
        self.ssh_username = "nvidia"

    def ssh_connect(self):
        self.ssh_client.connect(hostname = "172.16.2.14",username=self.ssh_username,password=self.ssh_password,port=self.ssh_port,timeout=10)
    def execu_cmd(self,cmd:str):
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
        # if stdout is not None:
        #     recv_data = stdout.read().decode('utf-8')
        #     print(f"[stdout recv] is {recv_data}")
        # if stderr is not None:
        #     error_data = stderr.read().decode()
        #     print(f"[stderr recv]:{error_data}")
        
    def ssh_close(self):
        self.ssh_client.close()
        print("ssh close done")
    def extract_full_name(self):
        pattern = r'"FullName":\s*"([^"]+)"'
        data_str = self.execu_cmd("head -n 21 /opt/deeproute/ADS.METADATA")[0]
        match = re.search(pattern, data_str)
        if match:
            print(match.group(1))
            return match.group(1)
    def extract_soc_version(self):
        data_str = self.execu_cmd("cat /etc/version")[0]
        return data_str
    def extract_tail(self):
        pattern = r'"ShortName":\s*"([^"]+)"'
        data_str = self.execu_cmd("tail  -n 25 /opt/deeproute/ADS.METADATA")[0]
        match = re.search(pattern, data_str)
        if match:
            short_name = match.group(1)
            print(f"提取的ShortName: {short_name}")
            return short_name
    def extract_dr_info(self):
        data_str = self.execu_cmd("cat /ota/source_package/dr_info.json")[0]
        # data_json = json.loads(data_str)
        return data_str
    def extract_gwm_version(self):
        data_str = self.execu_cmd("cat /opt/deeproute/driver/config/diagnostic/gwm*version.json")[0]
        # data_json = json.loads(data_str)

        return data_str

    def dem_status(self):
        data =  self.execu_cmd("systemctl status dem |head -11")[0]
        # data = data.replace("\r\n", "\n")
        return data


        

    def dem_restart(self, password = None):  
        if password is None:
            password = self.ssh_password
            print("pls enter password!!!using default password")
        stdin,stdout,stderr = self.ssh_client.exec_command("sudo systemctl restart dem",get_pty=True,timeout=20)
        time.sleep(1)
        print("waiting...")
        # if stdout.channel.recv_ready():
        #     out = stdout.read(1024).decode(errors='ignore')
        #     print(out)
        # if stderr.channel.recv_ready():
        #     output = stderr.read(1024).decode(errors='ignore')
        #     print(f"the output is {output}")
        # if "password" in output.lower():
        stdin.write(f"{password}\n")
        stdin.flush()  
        print("entered password")        

        for i in range(20,0,-1):
            print(f"dem restart... be patient...cnt:{i}s  ",end='\r')
            time.sleep(1)
        print("\r\n")
        return self.dem_status()


    def test(self):
        soc_info={}
        self.ssh_connect()
        head = self.extract_full_name()
        tail = self.extract_tail()
        soc_version = self.extract_soc_version()
        dem_status = self.dem_status()
        soc_gwm_version = self.extract_gwm_version()
        dr_info = self.extract_dr_info()
        restart_dem = self.dem_restart()
        self.ssh_close()
        soc_info = {
            "head-ADS.METADATA":head,
            "tail-ADS.METADATA":tail,
            "SOC_version":soc_version,
            "file_gwm_version":soc_gwm_version,
            "dem_status":dem_status,
            "dem_restart":restart_dem,
            "dr_info":dr_info
        }
        
        return soc_info
    
class Doip_client:
    def __init__(self):
        self.target_ip = "172.16.2.14"
        self.test_address = 0x1001
        self.func_address = 0xE400
        self.SOC_address = 0x1110
        self.P2_time = 5
        self.S3_time = 5
        self.DOIP_TYPE_DIAGNOSTIC = 0x8001  # diag req
        self.DOIP_TYPE_ALIVE_CHECK = 0x0005 # route active req

        self.default_key = bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF") 
        self.mask = 0x2044434C
        self.car_type = ''


    def client_setup(self):
        self.sock_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock_client.connect((self.target_ip,13400))
        self.sock_client.settimeout(self.P2_time)
        print("doip_client setup init done")

    
    def build_doip_message(self,message_type,data:str=''):
        doip_header = "02FD"
        doip_len = "00000000"
        message_type = "{:04x}".format(message_type)
        if data == '':
            print("pls enter the data")
            return -1
        if len(data)%2 !=0:
            print("error data format ,pls check it ")
            return -1
        frame = "{:04x}{:04x}".format(self.test_address,self.SOC_address) +data
        doip_len = "{:08x}".format(len(frame)//2)
        return  f"{doip_header}{message_type}{doip_len}{frame}"      
    def sock_close(self):
        self.sock_client.close()
        print("connection close...")


    def recv_doip_message(self):
        recv_data = self.sock_client.recv(256)
        # print("recv raw data:{}".format(' '.join(['{:02x}'.format(i) for i in recv_data]) ))
        recv_data = bytes.hex(recv_data)
        # print("recv_ACK from address:0x{} to 0x{}address with ACK {}".format(recv_data[16:20],recv_data[20:24],recv_data[24:]))
        recv_data_1 = self.sock_client.recv(2048)
        src_addr = int.from_bytes(recv_data_1[8:10], byteorder='big') 
        dest_addr = int.from_bytes(recv_data_1[10:12], byteorder='big')
        UDS_data = recv_data_1[12:]
        print("recv UDS data:{}".format(' '.join(['{:02x}'.format(i) for i in recv_data_1]) ))
        # print("[Source address]:0x{:04x},[Target address]:0x{:04x}".format(src_addr,dest_addr))
        print("[recv UDS frame]:{}".format(' '.join(['0x{:02x}'.format(i) for i in recv_data_1[12:]])))
        return ({
            'sid':int(UDS_data[0]),
            'data':[(i) for i in UDS_data[1:]],
            'len':len(UDS_data)
        })


    def route_active(self):
        act_frame = "02fd"+f"{self.DOIP_TYPE_ALIVE_CHECK:04x}"+"0000000B"+f"{self.test_address:04x}"+"E200000000"+"FFFFFFFF"
        # print(act_frame)
        self.sock_client.sendall(bytes.fromhex(act_frame))
        recv_data = self.sock_client.recv(512)
        recv_data = bytes.hex(recv_data)
        print("routing active")
        # print(recv_data)

    def get_key(self,seed:list):
        """
        计算密钥
        """
        real_seed = 0
        for data in seed:
            real_seed = (real_seed<<8)|data

        for _ in range(35):
            if real_seed & 0x80000000:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
                real_seed ^= self.mask
            else:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
        return real_seed


    def aes128_cmac_generate_key(self,seed: bytes) -> bytes:

        # print(f"len is {len(seed)}")
        # print(f"the seed is {seed.hex()}")
        if len(self.default_key) != 16:
            raise ValueError("pincode必须是16字节长度")
        if len(seed) != 16:
            raise ValueError("seed必须是16字节长度")
        
        c = cmac.CMAC(algorithms.AES(self.default_key), backend=default_backend())
        
        c.update(seed)
        
        return c.finalize()
    
    def data_tansfer_ascii(self,data:str):
        ascii_str = ''.join([chr(i) for i in data])
        print(ascii_str)
        return ascii_str
        ...
    def send_uds_req(self,SID:int,sub_func:int=None,data:str=None):
        
        uds_data = f"{SID:02x}"
        if sub_func is not None:
            uds_data +=f"{sub_func:02x}"
        if data is not None:
            uds_data+=data
        frame = self.build_doip_message(self.DOIP_TYPE_DIAGNOSTIC,uds_data)
        print("[Send data]:SID:0x{:02x},Data:{}".format(SID,([uds_data[i:i+2] for i in range(2,len(uds_data),2)])))
        self.sock_client.send(bytes.fromhex(frame))
        return self.recv_doip_message()
        ...

    

    def DiagnosticSessionControl(self,session:int):
        self.send_uds_req(0x10,session)


    def hard_reset(self):
        self.send_uds_req(0x11,0x01)
    def security_access(self,level:int):
        frame = self.send_uds_req(0x27,sub_func=level)
        seed = frame['data'][1:]
        if level == 0x01:
            self.mask = 0x2044434C
        elif level ==0x19:
            self.mask = 0x194C4344
        # print(frame)
        if frame['len']-2 ==4:

            key = self.get_key(seed)
            self.send_uds_req(0x27,level+1,format(key,'08x'))
            ...
        elif frame['len']-2 ==16:
            key = self.aes128_cmac_generate_key(bytes(seed))
            self.send_uds_req(0x27,level+1,key.hex().upper())
            ...

        else:
            print(f"[recv UDS frame]:{frame}")

            ...
    def DID_write(self,did:str,data):
        if not isinstance(did,str):
            print("error type input!!!")
            return -1
        
        frame = self.send_uds_req(0x2e,data=(did+data))
        return frame

    def write_F1B1_car_config_VIN(self,car_type):
        self.car_type = car_type
        if car_type == "P03":
            peizhizi = "14000001" + "00" * 62
        elif car_type == "P03A":
            peizhizi = "14000003" + "00" * 62
        elif car_type == "P03-F":
            peizhizi = "1C000001" + "00" * 62
        elif car_type == "P03A-F":
            peizhizi = "1C000003" + "00" * 62
        elif car_type == "P02":
            peizhizi = "15000001" + "00" * 62
        elif car_type == "P02A":
            peizhizi = "15000003" + "00" * 62
        elif car_type == "D03B":
            peizhizi = "16000001" + "00" * 62
        elif car_type == "D03A":
            peizhizi = "16000003" + "00" * 62
        elif car_type == "EC15":
            peizhizi = "0E000000" + "00" * 62
        elif car_type == "EC15S":
            peizhizi = "1B000000" + "00" * 62
        elif car_type == "C01-T":
            peizhizi = "17000000" + "00" * 62
        elif car_type == "DE09":
            peizhizi = "06000000" + "00" * 62
        elif car_type == "M81-3":
            peizhizi = "04000000" + "00" * 62
        elif car_type == "M82":
            peizhizi = "05000000" + "00" * 62
        elif car_type == "M83-1":
            peizhizi = "02000000" + "00" * 62
        elif car_type == "M82-FZ":
            peizhizi = "11000000" + "00" * 62
        elif car_type == "C01":
            peizhizi = "03000000" + "00" * 62
        else:
            print("[ERROR]!!! wrong car type!!! pls double check it")
            print("当前支持的车型对应配置字有：\n"
            "\tP03\n" 
            "\tP03A\n" 
            "\tP03-F   P03(降油耗版本)\n" 
            "\tP03A-F  P03A(酱油号版本)\n" 
            "\tP02\n" 
            "\tP02A\n"
            "\tD03B\n"
            "\tD03A\n"
            "\tEC15\n"
            "\tEC15S\n"
            "\tC01-T\n"
            "\tDE09\n"
            "\tM81-3\n"
            "\tM8\n"
            "\tM83-1\n"
            "\tM82-FZ\n"
            "\tC01\n")


            raise ValueError(f"未知的车型类型: {car_type},请重新尝试！！！")
        self.DiagnosticSessionControl(0x03)
        self.security_access(0x01)
        
        self.DID_write("F190","3837363534333231393837363534333231")
        resp = self.DID_write('F1B1', peizhizi)
        if resp["sid"] == 0x6e:
            self.hard_reset()
            print("[LOG]:write F1B1 car_type success!!!already reset ADCU for reloading car_tye") 
            return f"already inject car_type {self.car_type} and vin"
        else:
            ...

    def check_guanzhuang_version(self):
        gwm_version = self.send_uds_req(0x22,data="F189")
        gwm_software_info=self.send_uds_req(0x22,data="F1BC")
        gwm_Calibration_version=self.send_uds_req(0x22,data="F1C0")
        

        return{
            "gwm_version":self.data_tansfer_ascii(gwm_version.get('data')[2:]),
            "gwm_software_infomation":self.data_tansfer_ascii(gwm_software_info.get('data')[2:]),
            "gwm_Calibration_version":self.data_tansfer_ascii(gwm_Calibration_version.get('data')[2:])
        }
        
        
    



class FeishuRobot:
    def __init__(self, webhook_url):
        """初始化飞书机器人，需要传入Webhook地址"""
        self.webhook_url = webhook_url
        self.headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

    def send_text(self, content, at_all=False, at_users=None):
        """
        发送文本消息
        :param content: 消息内容
        :param at_all: 是否@所有人
        :param at_users: 需要@的用户open_id列表（可选）
        """
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        
        # 处理@逻辑
        if at_all:
            data["content"]["text"] += " @所有人"
            data["at"] = {"is_at_all": True}
        elif at_users:
            for user_id in at_users:
                data["content"]["text"] += f" <at user_id=\"{user_id}\"></at>"
            data["at"] = {"user_id": at_users}
        
        return self._send_request(data)

    def send_card(self, title, content, btn_text="查看详情", btn_url=None):
        """
        发送卡片消息
        :param title: 卡片标题
        :param content: 卡片内容（支持简单HTML标签）
        :param btn_text: 按钮文本
        :param btn_url: 按钮链接（可选）
        """
        elements = [{"tag": "div", "text": {"tag": "lark_md", "content": content}}]
        
        # 添加按钮
        if btn_url:
            elements.append({
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": btn_text},
                    "url": btn_url,
                    "type": "primary"
                }]
            })
        
        data = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": elements
            }
        }
        
        return self._send_request(data)

    def _send_request(self, data):
        """发送请求到飞书Webhook"""
        try:
            response = requests.post(
                url=self.webhook_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            result = response.json()
            
            if result.get("code") == 0:
                print("消息发送成功")
                return True
            else:
                print(f"消息发送失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"发送请求出错: {str(e)}")
            return False        
        

class Serial_device():
    #check if there are any thread occupied serial device!!!
    def __init__(self):
        self.ser = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=115200,
            bytesize=serial.EIGHTBITS,  # 8位数据位
            parity=serial.PARITY_NONE,   # 无校验位
            stopbits=serial.STOPBITS_ONE,  # 1位停止位
            timeout=1  # 超时时间（秒）
        )

        self.rx_thraed = None
        self.rx_buffer_size  = 2048
        self.rx_callback = None

    def close(self):
        print("serial device close")
        self.ser.close()

    def read_data(self):
        data = None
        if not self.ser or not self.ser.is_open:
            print("[WARNING] 串口未打开，无法读取数据")
            return ""  # 返回空字符串，而非-1
        time.sleep(0.5)
        if self.ser.in_waiting >= 30:
            data =self.ser.read(self.ser.in_waiting)
            print("recv data...")
            # print(f"Received {len(data)} bytes: {data}")

            return data.decode()
        return ""
        ...
    
    def send_data(self,data=None):
        if not self.ser.is_open:
            self.ser.open()
        else:
            
            print(f"已打开串口:/dev/ttyUSB0 (波特率: 115200)")
        if isinstance(data,str):
            data = data.encode()
        bytes_sent = self.ser.write(data)
        print(f"发送成功，共发送 {bytes_sent} 字节: {data.decode() if isinstance(data, bytes) else data}")
        self.ser.flush()
        time.sleep(0.3)

    def check_mcu_version(self):
        data = None
        version_start_mark = "Shell> version\r\r\n"
        self.send_data("version\r\n")
        data = self.read_data()
        if data is not None:
            start_index = data.find(version_start_mark)
            if start_index == -1:
                print("[ERROR1]could not find the version label!!!")
                return -1
            else:
                content_start = start_index + len(version_start_mark)
                content_end = data.find(" ",content_start)

            if content_end == -1 :
                extracted_content = data[content_start:].strip()
                print("[ERROR2]could not find the version label!!!")   
                return -1
            else:
                extracted_content = data[content_start:content_end].strip()

                print("version read success...")
                print(f"read versio is {extracted_content[4:]}")
        self.close()

        return extracted_content
        ...

    def check_switch_version(self):
        data = None
        version_start_mark = "[SWITCH]"
        self.send_data("switch\r\n")
        data = self.read_data()
        if data is not None:
            content_start_raw = data.find(version_start_mark)
            if content_start_raw == -1:
                print("[ERROR1]could not find switch version \r\n")
                
            else:
                content_start_raw = content_start_raw + len(version_start_mark)
                end_content = data.find("\r\n",content_start_raw)
            if end_content == -1:
                print("[ERROR2]could not find the version label!!!")   
                return -1
            else:
                switch_1 = data[content_start_raw:end_content]
                print("version read success...")
                print(f"switch_1 version is {switch_1}")
                sec_data = data.find("[SWITCH]",content_start_raw)
                if sec_data ==-1:
                    return switch_1
                else:
                    start_index = sec_data+len("[SWITCH]")
                    end_content = data.find("\r\n",start_index)
                if end_content ==-1:
                    print("[ERROR2]could not find the version label!!!")   
                    return -1
                else:
                    switch_2 = data[start_index:end_content]
                    print("version read success...")
                    print(f"switch_2 version is {switch_2}")
                    return(switch_1,switch_2)
        self.close()





class Feishu_API():
    def __init__(self,spreadsheet_token=None,sheet_id=None):
        self.App_ID = "cli_a72719d632be901c"        #申请的app_id
        self.App_Secret = "MWxgknshTRR5pIAgXDdDmhRwmIQdMdbN"
        self.spreadsheet_token = spreadsheet_token
        self.sheet_id = sheet_id


    

    def get_tenant_access_token(self):
        HTTP_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        Request_header = {
            "Content-Type":"application/json; charset=utf-8"
        }
        Request_BODY = {
            "app_id":self.App_ID,
            "app_secret":self.App_Secret
        }
        response = requests.post(HTTP_URL,headers=Request_header,data=json.dumps(Request_BODY))
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("tenant_access_token")
        else:
            print("access no found") 
        return -1
    

    def get_spreadsheet_info(self):
        HTTP_URL = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/"+self.spreadsheet_token
        Request_header = {
            "Authorization":"Bearer "+self.get_tenant_access_token(),
            "Content-Type":"application/json; charset=utf-8"
        }
        response = requests.get(HTTP_URL,headers=Request_header)
        if response.status_code == 200:
            token_data = response.json()
            print(token_data)
            return token_data
        else:
            print("access no found") 
        return -1
    
    def get_sheet_info(self):
        HTTP_URL = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/"+self.spreadsheet_token+"/sheets/query"
        Request_header = {
            "Authorization":"Bearer "+self.get_tenant_access_token(),
            "Content-Type":"application/json; charset=utf-8"
        }
        response = requests.get(HTTP_URL,headers=Request_header)
        if response.status_code == 200:
            token_data = response.json()
            print(token_data)
            return token_data
        else:
            print("access no found") 
        return -1
    
    def write_data_sheet(self,data_range=None,data_value=None):
        HTTP_URL = "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/"+self.spreadsheet_token+"/values"
        Request_header = {
            "Authorization":"Bearer "+self.get_tenant_access_token(),
            "Content-Type":"application/json; charset=utf-8"
        }

        if isinstance(data_value, str):
        # 如果是字符串，将其转换为二维数组（每个字符占一格）
            values = [[data_value]]
        elif isinstance(data_value, list):
        # 如果是列表，确保是二维数组
            if not data_value or isinstance(data_value[0], list):
                values = data_value  # 已经是二维数组
            else:
                values = [data_value]  # 一维列表转换为二维
        else:
        # 其他类型（如数字）转换为字符串
            values = [[str(data_value)]]
        write_content={
            'range':f"{self.sheet_id}!{data_range}",
            'values':values
        }
        requset_body = {'valueRange':write_content}
        # print(requset_body)
        response=requests.put(HTTP_URL,headers=Request_header,json=requset_body)
        if response.status_code == 200:
            token_data = response.json()
            return 0
        else:
            print("access no found") 
        return -1
    
    def read_data_sheet(self,data_range=None):

        data_range = f"{self.sheet_id}!{data_range}"
        print(data_range)
        HTTP_URL = "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/"+self.spreadsheet_token+"/values/"+data_range
        Request_header = {
            "Authorization":"Bearer "+self.get_tenant_access_token(),
            "Content-Type":"application/json; charset=utf-8"
        }
        response=requests.get(HTTP_URL,headers=Request_header)
        if response.status_code == 200:
            values = response.json()['data']['valueRange']['values']
            return values
        return "error"

if __name__== '__main__':
    if len(sys.argv)>1:
        car_type1 = sys.argv[1]
    else:
        print("dont find car type ")

        exit(-1)
    if car_type1 =='reset':
        test = Doip_client()
        test.client_setup()
        test.route_active()
        test.hard_reset()
        exit(0)
    test = Doip_client()
    test.car_type = car_type1
    test.client_setup()
    test.route_active()
    test.write_F1B1_car_config_VIN(car_type1)
    for i in range(80,0,-1):
        print(f"ADCU start cnt:{i}s  ",end='\r')
        time.sleep(1)

    serial1 = Serial_device()
    serial_mcu = serial1.check_mcu_version()
    serial_switch = serial1.check_switch_version()
    test.client_setup()
    test.route_active()
    doip_version=test.check_guanzhuang_version()
    print(f"CAR TYPE IS {car_type1}")
    TES = Ssh_client(car_type=car_type1)
    test_data = TES.test()
    print(f"the dem status is \r\n {test_data['dem_restart']}")
    
    formatted_json = json.dumps(test_data, indent=4, ensure_ascii=False)
    print(test_data)
    test.sock_close()
    # test_robot = Feishu_API(spreadsheet_token="J6oEsu8NnhM9VotJu1jcObjznhf",sheet_id="9BWBrS")
    test_robot = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/86f13735-aa8e-4dc1-aa6a-258177111a1e")
    test_robot.send_text(
    content=f"--------------------- can inject test ---------------------\r\n\
\r\n\
--------------------- 1. serial read - MCU ---------------------\r\n\
{serial_mcu}  \r\n\
\r\n\
--------------------- 2. serial read - switch ---------------------\r\n\
{serial_switch} \r\n\
\r\n\
--------------------- 3. head ADS-METADATA ---------------------\r\n\
{test_data['head-ADS.METADATA']}\r\n\
\r\n\
--------------------- 4. tail ADS-METADATA ---------------------\r\n\
{test_data['tail-ADS.METADATA']}\r\n\
\r\n\
--------------------- 5. SOC version ---------------------\r\n\
{test_data['SOC_version']} \r\n\
\r\n\
--------------------- 6. file_gwm_version ---------------------\r\n\
GWM 版本：{test_data['file_gwm_version']}\r\n\
--------------------- 7. DEM status ---------------------\r\n\
{test_data['dem_status']}  \r\n\
\r\n\
--------------------- 8. read dr_info ---------------------\r\n\
{test_data['dr_info']}\r\n\
\r\n\
--------------------- 9.DOIP read version ---------------------\r\n\
 gwm_version:{doip_version['gwm_version']}\r\n\
 gwm_software_infomation:{doip_version['gwm_software_infomation']}\r\n\
 gwm_Calibration_version:{doip_version['gwm_Calibration_version']}\r\n\
# --------------------- 10. DEM restart status ---------------------\r\n\
{test_data['dem_restart']} \r\n\
\r\n"
)



    # content="just a test[偷笑]",
    # btn_text="查看详情",
    # btn_url="www.baidu.com")
    # test_robot.send_text("[偷笑]")




    # swt_version = serial1.check_switch_version()
    # print(swt_version)
    # test.get_spreadsheet_info()
    # abc = test.get_sheet_info()
    # test.write_data_sheet("A1:A1",[['FAIL']])
    # A =  test.read_data_sheet("A1:A1")
    # print(A)

