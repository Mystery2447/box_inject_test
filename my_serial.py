import serial
import re
import time
from typing import Optional, Union, Tuple


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
            self.ser.reset_input_buffer() 
            bytes_sent = self.ser.write(data)
            self.ser.flush()  # 确保数据发送完成
            print(f"发送成功: {bytes_sent} 字节")
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False
    def send_and_verify(self, data: str, expect: str = None, max_retries: int = 3,
                        read_wait: float = 2.0, retry_delay: float = 1.0) -> bool:
        """
        发送命令并通过回显确认：设备会回显收到的命令，取命令第一个词在回显中比对。
        :param data: 发送的命令字符串
        :param expect: 回显中期望出现的关键字（默认取命令第一个词）
        :param max_retries: 最大重试次数
        :param read_wait: 每次等待回读的最长时间（秒）
        :param retry_delay: 重试间隔（秒）
        :return: 确认成功返回 True，超出重试次数返回 False
        """
        if expect is None:
            expect = data.strip().split()[0]

        for attempt in range(1, max_retries + 1):
            if not self.send_data(data):
                print(f"[WARN] send_and_verify: 发送失败 (attempt {attempt}/{max_retries})")
                time.sleep(retry_delay)
                continue

            time.sleep(0.3)
            resp = self.read_data(min_bytes=1, max_wait=read_wait) or ""

            if expect.lower() in resp.lower():
                print(f"[INFO] send_and_verify: '{expect}' 回显确认成功 (attempt {attempt}/{max_retries})")
                return True

            print(f"[WARN] send_and_verify: '{expect}' 未在回显中找到 "
                  f"(attempt {attempt}/{max_retries}), resp: {resp[:80].strip() or '(empty)'}")
            if attempt < max_retries:
                time.sleep(retry_delay)

        print(f"[ERROR] send_and_verify: '{expect}' 经 {max_retries} 次尝试仍未确认")
        return False

    def get_version(self, cmd: str = "version\r\n", max_retries: int = 3, retry_delay: float = 1.0) -> Optional[Union[str, tuple]]:
        """
        获取版本号，支持重试机制，自动识别命令类型
        
        :param cmd: 查询命令 ("version\r\n" 或 "switch\r\n")
        :param max_retries: 最大重试次数
        :param retry_delay: 重试间隔（秒）
        :return: 
            - version命令: 返回版本号字符串
            - switch命令: 返回元组 (version_a, version_b) 或单个版本号
            - 失败返回None
        """
        # 根据命令类型定义不同的正则表达式模式
        if "switch" in cmd.lower():
            patterns = [
                # 匹配 C01_S-6113_250819_D3F709 或 ADC4.0_S-5192A_260129_3A629 格式
                r'(?:ADC[\d\.]+|C\d+)_S-\d+[A-Za-z]?_[\d]+_[A-F0-9]+',
                # 匹配 ADC4.0_S_260304_7165EB 或 C01_S_xxxxxx_xxxxxx 格式
                r'(?:ADC[\d\.]+|C\d+)_S-?[A-Z0-9]*_?[\d]+_[A-F0-9]+',
                # 最通用的匹配：ADC/C01开头，包含_S，后面跟版本信息
                r'(?:ADC[\d\.]+|C\d+)_S[_-][A-Z0-9_-]+',
            ]
        else:
            patterns = [
                # 匹配 C01_MCU_R6.03.31_260331_780FB7 或 ADC4.0_MCU_R6.03.31_260331_780FB7 格式
                r'(?:ADC[\d\.]+|C\d+)_MCU_R[\d\.]+_\d+_[A-F0-9]+',
                # 匹配 ADC4.0_MCU_6.03.31_260331_780FB7 或 C01_MCU_6.03.31_260331_780FB7 格式
                r'(?:ADC[\d\.]+|C\d+)_MCU_[\d\.]+_\d+_[A-F0-9]+',
                # 最通用的匹配
                r'(?:ADC[\d\.]+|C\d+)_MCU_R?[\d\._]+[A-F0-9]*',
            ]
        
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"\n[重试 {attempt}/{max_retries-1}] 重新获取版本号...")
                time.sleep(retry_delay)
                
                # 清空缓冲区
                if self.is_open() and self.ser.in_waiting > 0:
                    self.ser.read(self.ser.in_waiting)
                    print("[INFO] 已清空缓冲区")
            
            # 发送命令
            if not self.send_data(cmd):
                print(f"[ERROR] 发送命令失败 (尝试 {attempt + 1})")
                continue
            
            # 等待设备响应
            time.sleep(0.5)
            
            # 读取响应数据
            response = self.read_data(min_bytes=10, max_wait=2.0)
            
            if not response:
                print(f"[WARNING] 未收到设备响应 (尝试 {attempt + 1})")
                continue
            
            # 提取所有匹配的版本号
            matched_versions = []
            for pattern in patterns:
                matches = re.findall(pattern, response)
                if matches:
                    matched_versions.extend(matches)
            
            # 去重并保持顺序
            unique_versions = []
            for v in matched_versions:
                if v not in unique_versions:
                    unique_versions.append(v)
            
            if unique_versions:
                print(f"[INFO] 提取到版本号: {unique_versions}")
                
                # 如果是 switch 命令，返回元组
                if "switch" in cmd.lower():
                    if len(unique_versions) >= 2:
                        # 尝试识别 5192A 和 5192B
                        version_a = next((v for v in unique_versions if '5192A' in v), None)
                        version_b = next((v for v in unique_versions if '5192B' in v), None)
                        
                        # 如果没有5192A/B标识，按顺序返回前两个
                        if not version_a and len(unique_versions) >= 2:
                            return (unique_versions[0], unique_versions[1])
                        
                        if version_a and version_b:
                            return (version_a, version_b)
                    
                    # 只有一个版本时返回元组（第二个为None）
                    return (unique_versions[0], None) if len(unique_versions) == 1 else None
                else:
                    # version 命令返回字符串
                    return unique_versions[0]
            
            # 如果响应中包含系统日志，提示并重试
            if any(keyword in response for keyword in ["buffer overflow", "abnormal", "cpu_load"]):
                print(f"[WARNING] 收到系统日志而非版本信息: {response[:80]}...")
            else:
                print(f"[WARNING] 未从响应中提取到版本号 (尝试 {attempt + 1})")
                print(f"[DEBUG] 原始响应: {response[:100]}")
        
        print(f"[ERROR] 经过 {max_retries} 次尝试后仍未获取到版本号")
        return None
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
    mcu_data = test.get_version(cmd='version\r\n',max_retries=5,retry_delay=1)
    switch_data = test.get_version(cmd='switch\r\n',max_retries=5,retry_delay=1)
    print(f"获取到的MCU版本信息: {mcu_data}")
    print(f"获取到的版本信息: {switch_data}")
