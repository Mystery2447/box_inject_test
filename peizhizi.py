import socket
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import cmac
import sys
import subprocess


peizhizi_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


peizhizi_map = {
    # 原有配置
    "P03": "1400000100000000000041" + "00" * 55,
    "P03A": "14000003" + "00" * 62,
    "P03-F": "1C000001" + "00" * 62,  # 降油耗版本
    "P03A-F": "1C000003" + "00" * 62,  # 酱油号版本
    "P02": "15000001" + "00" * 62,
    "P02A": "15000003" + "00" * 62,
    "D03B": "16000001" + "00" * 62,
    "D03A": "16000003" + "00" * 62,
    "EC15": "0E000000" + "00" * 62,
    "EC15S": "1B000000" + "00" * 62,
    "C01-T": "17000000" + "00" * 62,
    "DE09": "06000000" + "00" * 62,
    "M81-3": "04000000" + "00" * 62,
    "M82": "05000000" + "00" * 62,
    "M83-1": "02000000" + "00" * 62,
    "M82-FZ": "11000000" + "00" * 62,
    "C01": "03000000" + "00" * 62,
    "C061": "1E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(' ',""), # 第36字节为20 (36字节 = 34个00 + 2字符 = 35字节位置)
    "C062": "21000000" + "00" * 62,
    "C063": "1E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(' ',''),  # 第36字节为40
    "DE08": "18000000" + "00" * 62,
    "C06A1": "1F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(' ',''),  # 第36字节为20
    "C06A2": "1F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(' ',''),  # 第36字节为40
    "C06A3": "22000000" + "00" * 62
}


def execute(command: str) -> None:
        print(command)
        subprocess.run(command, shell=True)



# def set_network_vlan5(net:str):
#     execute(f"sudo ip link add link {net} name mgbe3_0.5 type vlan id 5 >/dev/null 2>&1 || true")
#     execute(f"sudo ip link set mgbe3_0.5 type vlan egress 0:2 1:2 2:2 3:2 4:2 5:2 6:2 7:2")
#     execute(f"sudo ip address add 172.16.5.58/16 dev mgbe3_0.5 >/dev/null 2>&1 || true")
#     execute(f"sudo ip link set dev mgbe3_0.5 address 02:47:57:4d:00:58")
#     execute(f"sudo ip link set dev mgbe3_0.5 up")
#     print("vlan 5 network setting complete...")

def set_network_vlan2(net:str):
    execute(f"sudo ip link add link {net} name enp3s0.2 type vlan id 2 >/dev/null 2>&1 || true")
    execute(f"sudo ip link set enp3s0.2 type vlan egress 0:2 1:2 2:2 3:2 4:2 5:2 6:2 7:2")
    execute(f"sudo ip addr add 172.16.2.58/24 dev enp3s0.2 >/dev/null 2>&1 || true")
    execute(f"sudo ip link set dev enp3s0.2 address 02:47:57:4d:00:58")
    execute(f"sudo ip link set dev enp3s0.2 up")
    print("vlan 2 network setting complete...")

def string_to_hex(data:str)->list:
    hex_list = [f"{ord(i):02x}" for i in data  ]
    
    return hex_list

class DoipClient:
    def __init__(self):
        self.target_ip = "172.16.2.14"
        self.test_address = 0x1001
        self.func_address = 0xE400
        self.SOC_address = 0x1110
        self.P2_time = 5
        self.S3_time = 5
        self.DOIP_TYPE_DIAGNOSTIC = 0x8001  # 诊断请求
        self.DOIP_TYPE_ALIVE_CHECK = 0x0005  # 路由激活请求
        self.other_key = bytes.fromhex("456E68616E636544475F6B65795F3132")
        self.default_key = bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
        self.mask = 0x2044434C
        self.car_type = ''
        self.sock_client = None

    def client_setup(self):
        """初始化 DOIP 连接"""
        try:
            
            self.sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock_client.settimeout(self.P2_time)
            self.sock_client.connect((self.target_ip, 13400))
            print("doip_client setup init done")
            return True
        except socket.timeout:
            #TIMEOUT
            error_msg = f"ERROR connection timeout target_IP :{self.target_ip}port :13400 timeout:{self.P2_time} s"
            print(f"[ERROR] {error_msg},pls check the network setting")
            self.sock_close()  

            return error_msg                 

    def build_doip_message(self, message_type, data: str = ''):
        """构建 DOIP 消息帧"""
        if not data:
            print("pls enter the data")
            return -1
        if len(data) % 2 != 0:
            print("error data format ,pls check it ")
            return -1

        doip_header = "02FD"
        frame = f"{self.test_address:04x}{self.SOC_address:04x}{data}"
        doip_len = f"{len(frame)//2:08x}"
        message_type_hex = f"{message_type:04x}"
        return f"{doip_header}{message_type_hex}{doip_len}{frame}"

    def sock_close(self):
        """关闭 DOIP 连接"""
        if self.sock_client:
            self.sock_client.close()
            print("DOIP connection close...")

    def recv_doip_message(self):
        """接收 DOIP 响应消息"""
        recv_data = self.sock_client.recv(256)
        recv_data = bytes.hex(recv_data)
        
        recv_data_1 = self.sock_client.recv(2048)

        if len(recv_data_1)>13:

            src_addr = int.from_bytes(recv_data_1[8:10], byteorder='big')
            dest_addr = int.from_bytes(recv_data_1[10:12], byteorder='big')

            UDS_data = recv_data_1[12:]
            
            # print("recv UDS data:{}".format(' '.join(['{:02x}'.format(i) for i in recv_data_1])))
            print("[recv UDS frame]:{}".format(' '.join(['0x{:02x}'.format(i) for i in UDS_data])))
            while UDS_data[0]==0x7f and UDS_data[2]==0x78:
                print("pending...")
                recv_data_1 = self.sock_client.recv(2048)
                UDS_data = recv_data_1[12:]
                print("[recv UDS frame]:{}".format(' '.join(['0x{:02x}'.format(i) for i in UDS_data])))
            return {
                'sid': int(UDS_data[0]),
                'data': [i for i in UDS_data[1:]],
                'len': len(UDS_data),
                'NRC':0
            }
        elif len(recv_data_1)==13:
            UDS_data = recv_data_1[12:]
            return {
                'sid': UDS_data[0],
                'data':UDS_data,
                'len': len(UDS_data),
                'NRC':UDS_data[2]
            }


    def route_active(self):
        """发送路由激活请求"""
        act_frame = f"02fd{self.DOIP_TYPE_ALIVE_CHECK:04x}0000000B{self.test_address:04x}E200000000FFFFFFFF"
        self.sock_client.sendall(bytes.fromhex(act_frame))
        self.sock_client.recv(512)
        print("routing active")

    def get_key(self, seed: list):
        """计算密钥（用于安全访问）"""
        real_seed = 0
        for data in seed:
            real_seed = (real_seed << 8) | data

        for _ in range(35):
            if real_seed & 0x80000000:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
                real_seed ^= self.mask
            else:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
        return real_seed

    def aes128_cmac_generate_key(self, seed: bytes) -> bytes:
        """AES128-CMAC 生成密钥"""
        if len(self.default_key) != 16:
            raise ValueError("pincode必须是16字节长度")
        if len(seed) != 16:
            raise ValueError("seed必须是16字节长度")

        c = cmac.CMAC(algorithms.AES(self.default_key), backend=default_backend())
        c.update(seed)
        return c.finalize()

    def data_tansfer_ascii(self, data: list):
        """字节列表转 ASCII 字符串"""
        ascii_str = ''.join([chr(i) for i in data])
        print(ascii_str)
        return ascii_str

    def send_uds_req(self, SID: int, sub_func: int = None, data: str = None):
        """发送 UDS 请求"""
        uds_data = f"{SID:02x}"
        if sub_func is not None:
            uds_data += f"{sub_func:02x}"
        if data is not None:
            uds_data += data

        frame = self.build_doip_message(self.DOIP_TYPE_DIAGNOSTIC, uds_data)
        print(f"[Send data]:SID:0x{SID:02x},Data:{[uds_data[i:i+2] for i in range(2, len(uds_data), 2)]}")
        self.sock_client.send(bytes.fromhex(frame))
        return self.recv_doip_message()

    def DiagnosticSessionControl(self, session: int):
        """诊断会话控制"""
        self.send_uds_req(0x10, session)

    def hard_reset(self):
        """硬件复位"""
        self.send_uds_req(0x11, 0x01)

    def security_access(self, level: int):
        """安全访问（密钥验证）"""
        frame = self.send_uds_req(0x27, sub_func=level)
        seed = frame['data'][1:]

        if level == 0x01:
            self.mask = 0x2044434C
        elif level == 0x19:
            self.mask = 0x194C4344
        elif level == 0x29:
            self.mask = 0x294C4344
        elif level == 0x35:
            self.mask = 0x3644434C

        if frame['len'] - 2 == 4:
            key = self.get_key(seed)
            self.send_uds_req(0x27, level + 1, format(key, '08x'))
        elif frame['len'] - 2 == 16:
            key = self.aes128_cmac_generate_key(bytes(seed))
            recv_frame = self.send_uds_req(0x27, level + 1, key.hex().upper())
            if recv_frame['NRC']!=0:
                print(f"WARNNING:security unlock fail with NRC {recv_frame['NRC']},plz inject default key & rerun script!!!")
                return -1 
        else:
            print(f"[recv UDS frame]:{frame} without unlock")

    def DID_read(self,did:str):
        return self.send_uds_req(0x22,data=did)

    def DID_write(self, did: str, data: str):
        """写入 DID 数据"""
        if not isinstance(did, str):
            print("error type input!!!")
            return -1
        return self.send_uds_req(0x2e, data=(did + data))



    def write_F1B1_car_config_VIN(self):
        """写入 F1B1 车型配置"""
        peizhizi_map = {
    # 基础配置 - 只需要第一个字节的
    "P03": "1400000100000000000041" + "00" * 55,      # 8 + 124 = 132字符
    "P03A": "14000003" + "00" * 62,
    "P03-F": "1C000001" + "00" * 62,
    "P03A-F": "1C000003" + "00" * 62,
    "P02": "15000001" + "00" * 62,
    "P02A": "15000003" + "00" * 62,
    "D03B": "16000001" + "00" * 62,
    "D03A": "16000003" + "00" * 62,
    "D037": "23000000" + "00" * 62,
    "EC15": "0E000000" + "00" * 62,
    "EC15S": "1B000000" + "00" * 62,
    "C01-T": "17000000" + "00" * 62,
    "C062": "21000000" + "00" * 62,
    "C06A3": "22000000" + "00" * 62,
    "M81-3": "04000000" + "00" * 62,
    "M82": "05000000" + "00" * 62,
    "M83-1": "02000000" + "00" * 62,
    "M82-FZ": "11000000" + "00" * 62,
    "M81H": "2A000000" + "00" * 62,
    "C01": "03000000" + "00" * 62,
    "P01T": "24000003" + "00" * 62,
    "P01Z": "24000001" + "00" * 62,
    "DE061": "1A000700" + "00" * 62,
    "DE062": "1A000800" + "00" * 62,
    "DE06E": "27000000" + "00" * 62,
    "DE09": "06000000" + "00" * 62,
    "DE09U": "20000000" + "00" * 62,
    "DE09E": "28000000" + "00" * 62,
    "M81T": "2D000000" + "00" * 62,
    "M82T": "2E000000" + "00" * 62,
    "M83T": "2F000000" + "00" * 62,
    "B26": "0C000000" + "00" * 62,
    "B26E": "29000000" + "00" * 62,
    "B07": "2C000000" + "00" * 62,
    "B07E": "2B000000" + "00" * 62,
    
    # C061 - 第36字节(35)为20
    "C061": "1E 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # 第36字节为20 (36字节 = 34个00 + 2字符 = 35字节位置)
    "C062": "21 00 0D 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # C062 - 第3字节(2)为0D，第36字节(35)为40
    # C063 - 第3字节(2)为0C，第36字节(35)为40
    "C063": "1E 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C064 - 第3字节(2)为0D，第36字节(35)为40
    "C064": "1E 00 0D 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C06A1 - 第36字节(35)为20
    "C06A1": "1F 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C06A2 - 第36字节(35)为40
    "C06A2": "1F 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A1 - 第16字节(15)为10，第36字节(35)为20
    "B26A1": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 10 00 10 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A3 - 第16字节(15)为00，第36字节(35)为20
    "B26A3": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A2 - 第16字节(15)为10，第36字节(35)为60
    "B26A2": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 10 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 60 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A4 - 第16字节(15)为00，第36字节(35)为60
    "B26A4": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 60 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # DE07 - 第26字节(25)为01
    "DE07": "19 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 01 00 00 01 00 20 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # DE07 - 第26字节(25)为01
    
    # DE07U - 第26字节(25)为02
    "DE07U": "19 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 02 00 00 01 20 20 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # DE08 - 第26字节(25)为01
    "DE08": "18 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 01 00 00 01 80 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # DE08 - 第26字节(25)为01
    
    # DE08U - 第26字节(25)为02
    "DE08U": "18 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 02 00 00 01 80 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ","") # DE08U - 第26字节(25)为02,
    }
        if self.car_type not in peizhizi_map:
            print("[ERROR]!!! wrong car type!!! pls double check it")
            print("当前支持的车型对应配置字有：\n" + "\n".join([f"\t{k}" for k in peizhizi_map.keys()]))
            raise ValueError(f"未知的车型类型: {self.car_type}")

        peizhizi = peizhizi_map[self.car_type]
        self.DiagnosticSessionControl(0x03)
        self.security_access(0x01)
        self.DID_write("F190", "3837363534333231393837363534333231")
        resp = self.DID_write('F1B1', peizhizi)
        
        if resp["sid"] == 0x6e:
            self.hard_reset()
            print(f"[LOG]:write F1B1 car_type success!!!already reset ADCU for reloading car_type: {self.car_type}")
            return f"already inject car_type {self.car_type} and vin"
        else:
            print(f"[LOG]:write F1B1 car_type failed, resp: {resp}")
            return f"inject car_type {self.car_type} failed"




if __name__=='__main__':
    print("当前支持的车型对应配置字有：\n" + "\n".join([f"\t{k}" for k in peizhizi_map.keys()]))
    car_type = input("plz input car_type or custom CCP---输入对应车型(或输入custom使用自定义配置):")
    if car_type != "custom":
        if car_type not in peizhizi_map:
            print("[ERROR]!!! wrong car type!!! pls double check it")
            print("当前支持的车型对应配置字有：\n" + "\n".join([f"\t{k}" for k in peizhizi_map.keys()]))
            raise ValueError(f"未知的车型类型: {car_type}")
        test = DoipClient()
        test.car_type = car_type
        test.client_setup()
        test.route_active()
        test.write_F1B1_car_config_VIN()
        test.sock_close()
    else:
        print("eg:DE09---06 39 00 01 0a 6d 07 03 63 35 02 45 10 55 09 01 44 54 00 19 54 20 11 00 10 10 11 22 88 33 20 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
        temp_ccp = input("input 66 bytes ccp : ")

        temp_ccp = temp_ccp.replace(" ","")
        if len(temp_ccp)!=132:
            print("WARNNING:wrong length of CCP!!!plz double check it")
            exit(-1)
        test = DoipClient()
        test.car_type = car_type
        test.client_setup()
        test.route_active()
        test.DID_write("F1B1",temp_ccp)
        test.sock_close()
    # cartype =None
    # if len(sys.argv)>2:
    #     cartype = sys.argv[1]
    #     net = sys.argv[2]
    #     print(f"recv car type is {cartype},network is {net}")
    # elif len(sys.argv)==2:
    #     cartype = sys.argv[1]
    #     net = ""

    # else:
    #     cartype = 'C01'  
    #     print(f"using default setting car type {cartype}...")
    # test = DoipClient()
    # test.car_type = cartype
    # test.client_setup()
    # test.route_active()
    # test.write_F1B1_car_config_VIN()
    # test.sock_close()
    
    # data=  test.check_ota_progress()
    # print(data)
