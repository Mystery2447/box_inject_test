import serial
import serial.tools.list_ports
import time
ch1_off = b'\xA0\x01\x00\xA1'
ch1_on = b'\xA0\x01\x01\xA2'
ch2_off = b'\xA0\x02\x00\xA2'
ch2_on = b'\xA0\x02\x01\xA3'
ch3_off =b'\xA0\x03\x00\xA3'
ch3_on = b'\xA0\x03\x01\xA4'
ch4_off = b'\xA0\x04\x00\xA4'
ch4_on = b'\xA0\x04\x01\xA5'


def find_relay_com():
    ports = serial.tools.list_ports.comports()
    print("-" * 60)
    for port in ports:
        if("USB-SERIAL CH340" in port.description): 
            print(f"设备: {port.device}")           # COM口，如 COM3, COM8
            print(f"描述: {port.description}")       # 设备描述
            print(f"硬件ID: {port.hwid}")            # 硬件ID
            print(f"制造商: {port.manufacturer}")     # 制造商
            print(f"产品: {port.product}")            # 产品名称
            print(f"序列号: {port.serial_number}")    # 序列号
            print("-" * 60)

            return port.device
    print("❌ 未找到 继电器 设备，请检查连接！")
    return None






class Relay:
    """继电器控制类，提供串口通信接口来控制继电器的开关状态
    CH1---switch-A  剪断VCC,把GND串继电器
    CH2---switch-B  剪断VCC,把GND串继电器
    CH3---miniwiggler  把GND串继电器
    CH4---KL30 power supply  把KL30串继电器
    """
    def __init__(self, port: str):
        self.serial = serial.Serial(port, 9600,
                                    timeout=1,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE)
    def check_state(self):
        self.serial.write(b'\xff')
        ret = self.serial.read(40)
        return ret.decode(errors='ignore')
    def ch1_on(self):
        self.serial.write(ch1_on)
    def ch1_off(self):
        self.serial.write(ch1_off)
    def ch2_on(self):
        self.serial.write(ch2_on)
    def ch2_off(self):
        self.serial.write(ch2_off)
    def ch3_on(self):
        self.serial.write(ch3_on)
    def ch3_off(self):
        self.serial.write(ch3_off)
    def ch4_on(self):
        self.serial.write(ch4_on)
    def ch4_off(self):
        self.serial.write(ch4_off)
    def ch_all_on(self):
        self.ch1_on()
        self.ch2_on()
        self.ch3_on()
        self.ch4_on()
    def ch_all_off(self):
        self.ch1_off()
        self.ch2_off()
        self.ch3_off()
        self.ch4_off()
    def close(self):
        self.serial.close()


def test():
    r = Relay("COM8")
    print(r.check_state())
    r.ch1_on()
    r.ch2_on()
    print(r.check_state())
    time.sleep(2)
    r.ch_all_off()
    print(r.check_state())
    r.close()

if(__name__ == "__main__"):
    print(find_relay_com())