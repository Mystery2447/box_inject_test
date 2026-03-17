import serial
import time
from typing import Optional, Union, Tuple

# class Serial_device():
#     #check if there are any thread occupied serial device!!!
#     def __init__(self):
#         self.ser = serial.Serial(
#             port='/dev/ttyUSB0',
#             baudrate=115200,
#             bytesize=serial.EIGHTBITS,  # 8位数据位
#             parity=serial.PARITY_NONE,   # 无校验位
#             stopbits=serial.STOPBITS_ONE,  # 1位停止位
#             timeout=1  # 超时时间（秒）
#         )

#         self.rx_thraed = None
#         self.rx_buffer_size  = 2048
#         self.rx_callback = None

#     def close(self):
#         print("serial device close")
#         self.ser.close()

#     def read_data(self):
#         data = None
#         if not self.ser or not self.ser.is_open:
#             print("[WARNING] 串口未打开，无法读取数据")
#             return ""  # 返回空字符串，而非-1
#         time.sleep(0.5)
#         if self.ser.in_waiting >= 30:
#             data =self.ser.read(self.ser.in_waiting)
#             print("recv data...")
#             # print(f"Received {len(data)} bytes: {data}")

#             return data.decode()
#         return ""
#         ...
    
#     def send_data(self,data=None):
#         if not self.ser.is_open:
#             self.ser.open()
#         else:
            
#             print(f"已打开串口:/dev/ttyUSB0 (波特率: 115200)")
#         if isinstance(data,str):
#             data = data.encode()
#         bytes_sent = self.ser.write(data)
#         print(f"发送成功，共发送 {bytes_sent} 字节: {data.decode() if isinstance(data, bytes) else data}")
#         self.ser.flush()
#         time.sleep(0.3)

#     def check_mcu_version(self):
#         data = None
#         version_start_mark = "Shell> version\r\r\n"
#         self.send_data("version\r\n")
#         data = self.read_data()
#         if data is not None:
#             start_index = data.find(version_start_mark)
#             if start_index == -1:
#                 print("[ERROR1]could not find the version label!!!")
#                 return -1
#             else:
#                 content_start = start_index + len(version_start_mark)
#                 content_end = data.find(" ",content_start)

#             if content_end == -1 :
#                 extracted_content = data[content_start:].strip()
#                 print("[ERROR2]could not find the version label!!!")   
#                 return -1
#             else:
#                 extracted_content = data[content_start:content_end].strip()

#                 print("version read success...")
#                 print(f"read versio is {extracted_content[4:]}")
#         self.close()

#         return extracted_content
#         ...

#     def check_switch_version(self):
#         data = None
#         version_start_mark = "[SWITCH]"
#         self.send_data("switch\r\n")
#         data = self.read_data()
#         if data is not None:
#             content_start_raw = data.find(version_start_mark)
#             if content_start_raw == -1:
#                 print("[ERROR1]could not find switch version \r\n")
                
#             else:
#                 content_start_raw = content_start_raw + len(version_start_mark)
#                 end_content = data.find("\r\n",content_start_raw)
#             if end_content == -1:
#                 print("[ERROR2]could not find the version label!!!")   
#                 return -1
#             else:
#                 switch_1 = data[content_start_raw:end_content]
#                 print("version read success...")
#                 print(f"switch_1 version is {switch_1}")
#                 sec_data = data.find("[SWITCH]",content_start_raw)
#                 if sec_data ==-1:
#                     return switch_1
#                 else:
#                     start_index = sec_data+len("[SWITCH]")
#                     end_content = data.find("\r\n",start_index)
#                 if end_content ==-1:
#                     print("[ERROR2]could not find the version label!!!")   
#                     return -1
#                 else:
#                     switch_2 = data[start_index:end_content]
#                     print("version read success...")
#                     print(f"switch_2 version is {switch_2}")
#                     return(switch_1,switch_2)
#         self.close()

class Serial_device():
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=2):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout  # 延长超时时间，适应设备响应速度
        )
        self.rx_thread = None
        self.rx_buffer_size = 2048
        self.rx_callback = None

    def is_open(self) -> bool:
        """检查串口是否打开"""
        return self.ser and self.ser.is_open

    def open(self) -> bool:
        """打开串口（避免重复打开）"""
        if not self.is_open():
            try:
                self.ser.open()
                print(f"串口已打开: {self.ser.port} (波特率: {self.ser.baudrate})")
                return True
            except Exception as e:
                print(f"串口打开失败: {e}")
                return False
        return True

    def close(self):
        """关闭串口（仅在打开时操作）"""
        if self.is_open():
            self.ser.close()
            print("串口已关闭")

    def read_data(self, min_bytes: int = 1, max_wait: float = 2.0) -> str:
        """
        读取串口数据，优化版
        :param min_bytes: 最小读取字节数（避免因数据量小而丢弃）
        :param max_wait: 最大等待时间（秒），确保数据完整接收
        """
        if not self.is_open():
            print("[WARNING] 串口未打开，无法读取数据")
            return ""

        start_time = time.time()
        received_data = b""

        # 循环读取，直到获取足够数据或超时
        while (time.time() - start_time) < max_wait:
            # 读取当前可用数据
            if self.ser.in_waiting > 0:
                received_data += self.ser.read(self.ser.in_waiting)
                # 若已满足最小字节数，提前退出
                if len(received_data) >= min_bytes:
                    break
            # 短时间休眠，避免CPU占用过高
            time.sleep(0.01)

        if received_data:
            print(f"接收数据: {len(received_data)} 字节")
            return received_data.decode(errors='replace')  # 容错解码
        else:
            print("未接收到数据")
            return ""

    def send_data(self, data: Optional[Union[str, bytes]]) -> bool:
        """发送数据，增加错误处理"""
        if not data:
            print("发送数据为空")
            return False

        if not self.open():  # 确保串口已打开
            return False

        try:
            if isinstance(data, str):
                data = data.encode()
            bytes_sent = self.ser.write(data)
            self.ser.flush()  # 确保数据发送完成
            print(f"发送成功: {bytes_sent} 字节")
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def check_mcu_version(self, retries: int = 3) -> Optional[str]:
        """检查MCU版本，增加重试机制"""
        version_start_mark = "Shell> version\r\n"
        extracted_content=None
        for _ in range(retries):
            # 发送指令（确保结尾换行正确）
            if not self.send_data("version\r\n"):
                time.sleep(0.5)
                continue

            # 读取响应（MCU版本通常较短，最小10字节）
            data = self.read_data(min_bytes=10, max_wait=1.5)
            if not data:
                time.sleep(0.5)
                continue

            # 解析版本
            start_index = data.find(version_start_mark)
            if start_index == -1:
                print("[ERROR] 未找到版本标识")
                time.sleep(0.5)
                continue

            content_start = start_index + len(version_start_mark)
            content_end = data.find("Compile", content_start)
            if content_end == -1:
                extracted_content = data[content_start:].strip()
            else:
                extracted_content = data[content_start:content_end].strip()

            if extracted_content:
                print(f"MCU版本读取成功: {extracted_content}")
                return extracted_content

        print(f"重试{retries}次后仍失败")
        return None

    def check_switch_version(self, retries: int = 3) -> Union[None, str, Tuple[str, str]]:
        """检查交换机版本，增加重试机制"""
        version_mark = "[SWITCH]"
        
        for _ in range(retries):
            if not self.send_data("switch\r\n"):
                time.sleep(0.5)
                continue

            # 交换机可能返回多条数据，延长等待时间
            data = self.read_data(min_bytes=10, max_wait=2.0)
            if not data:
                time.sleep(0.5)
                continue

            # 解析第一个版本
            start1 = data.find(version_mark)
            if start1 == -1:
                print("[ERROR] 未找到switch版本标识")
                time.sleep(0.5)
                continue

            start1 += len(version_mark)
            end1 = data.find("\r\n", start1)
            if end1 == -1:
                print("[ERROR] 未找到版本结束标识")
                time.sleep(0.5)
                continue
            switch1 = data[start1:end1].strip()

            # 解析第二个版本（如果存在）
            start2 = data.find(version_mark, start1)
            if start2 == -1:
                print(f"switch1版本: {switch1}")
                return switch1

            start2 += len(version_mark)
            end2 = data.find("\r\n", start2)
            if end2 == -1:
                print(f"swithch1版本: {switch1}（未找到第二个版本）")
                return switch1

            switch2 = data[start2:end2].strip()
            print(f"switch1版本: {switch1}, switch2版本: {switch2}")
            return (switch1, switch2)

        print(f"重试{retries}次后仍失败")
        return None

if __name__ == '__main__':
    test = Serial_device()
    test.send_data("poweron\r\n")
