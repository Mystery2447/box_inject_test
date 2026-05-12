from flash_mcu import flash_mcu
from flash_switch import flash_switch
import sys
import time
import serial.tools.list_ports
from common.relay import find_relay_com, Relay
from common.utils import get_guanzhaung_pack_info
from remote_ssh import SSHRemoteController



if __name__ == "__main__":
    print("=== 全自动刷写工具 ===\n")
    print("input: python auto_flash.py <架构> <车型> <workflowID>")
    if(len(sys.argv) < 4):
        print("❌ 错误: 参数不足")
        print("usage: python auto_flash.py <架构> <车型> <workflowID>")
        print("example: python auto_flash.py THOR/ORINY/ORINX C01 3efe73e3-...")
        sys.exit(1)
    

    relay_port = find_relay_com()
    if not relay_port:
        print("❌ 错误: 未找到继电器设备")
        sys.exit(1)
    r = Relay(relay_port)
    print(f"✅ 继电器设备连接成功: {relay_port}")



    archecture = sys.argv[1].strip().lower()
    workflowId = sys.argv[3].strip()
    cartype = sys.argv[2].strip().upper()
    print(f"架构: {archecture}")
    print(f"workflowId: {workflowId}")
    print(f"车型: {cartype}")
    pack_info = get_guanzhaung_pack_info(workflowId)
    ssh_client = SSHRemoteController("10.24.97.156", "chenzefeng", "deeproute@123")
    ssh_client.connect()
    r.ch1_off()
    r.ch2_off()
    r.ch3_off()
    r.ch4_on()  # 连接KL30电源，保持域控通电
    print("✅ 继电器全断开\n")
    ret = ssh_client.send_serial_commands("/dev/ttyUSB0", ["poweron\\r\\n", "swtcmd hb 0\\r\\n"])
    if ret == False:
        print("❌ 监测域控上电失败，开始3次重试")
        retry_count = 0
        while retry_count < 3:
            r.ch4_off()  # 断开KL30电源
            time.sleep(2)  # 等待2秒钟确保完全断开
            r.ch4_on()   # 重新连接KL30电源，模拟重启
            print(f"✅ 域控重启成功，正在重试发送串口唤醒命令... (尝试次数: {retry_count + 1})")
            ret = ssh_client.send_serial_commands("/dev/ttyUSB0", ["poweron\\r\\n", "swtcmd hb 0\\r\\n"])
            if ret:
                print("✅ 串口唤醒命令发送成功！")
                break
            retry_count += 1
        print("❌ 监测域控上电失败，重试结束，流程终止")
        ssh_client.close()
        r.close()
        sys.exit(1)
    if((pack_info.get("sourceSwitchB",{}) !={})and (archecture == 'thor')):
        flag_switchb_en = True
    else:
        flag_switchb_en = False
    
    print("正在执行 SWITCH-A  线刷流程...")
    r.ch1_on()  # 打开继电器通道1，连接到 SWITCH-A
    ret = flash_switch(archecture, pack_info.get('sourceSwitch').get('uuid'))
    if ret:
        print("✅ SWITCH-A 刷写成功")
    else:
        print("❌ SWITCH-A 刷写失败，流程终止")
        ssh_client.close()
        r.close()
        sys.exit(1)
    if flag_switchb_en == True:
        print("正在执行 SWITCH-B 线刷流程...")
        r.ch1_off()  # 关闭通道1
        time.sleep(1)  # 等待继电器切换
        r.ch2_on()   # 打开通道2，连接到 SWITCH-B
        ssh_client.send_serial_commands("/dev/ttyUSB0", ["aurixreset\\r\\n", "swtcmd hb 0\\r\\n"])
        time.sleep(2)  # 等待设备重启
        ret = flash_switch(archecture, pack_info.get('sourceSwitchB').get('uuid'))
        if ret:
            print("✅ SWITCH-B 刷写成功")
        else:
            print("❌ SWITCH-B 刷写失败，流程终止")
            ssh_client.close()
            r.close()
            sys.exit(1)

    
    print("正在执行 MCU 刷写流程...")
    r.ch1_off()
    r.ch3_on()
    ret = flash_mcu(archecture, pack_info.get('sourceMcu').get('uuid'))
    if ret:
        print("✅ MCU 刷写成功")
        r.ch_all_off()
    else:
        print("❌ MCU 刷写失败，流程终止")
        ssh_client.close()
        r.ch1_off()
        r.ch3_off()
        r.ch2_off()
        r.ch4_on()  # 连接KL30电源，保持域控通电
        r.close()
        sys.exit(1)
    ## 域控硬件重启---控继电器
    print("正在重启域控...")
    r.ch_all_off()  # 断开所有连接
    time.sleep(5)  # 等待5秒钟确保完全断开
    r.ch4_on()   # 连接KL30电源，模拟重启
    print("✅ 域控重启成功")
    ret = ssh_client.send_serial_commands("/dev/ttyUSB0", "poweron\\r\\n")
    if ret == False:
        print("❌ 发送串口唤醒命令失败，请求重启...重试3次")
        retry_count = 0
        while retry_count < 3:
            r.ch4_off()  # 断开KL30电源
            time.sleep(5)  # 等待5秒钟确保完全断开
            r.ch4_on()   # 重新连接KL30电源，模拟重启
            print(f"✅ 域控重启成功，正在重试发送串口唤醒命令... (尝试次数: {retry_count + 1})")
            ret = ssh_client.send_serial_commands("/dev/ttyUSB0", "poweron\\r\\n")
            if ret:
                print("✅ 串口唤醒命令发送成功！")

                break
            retry_count += 1
        if retry_count == 3:
            print("❌ 发送串口唤醒命令失败，重试结束，流程终止")
            ssh_client.close()
            r.close()
            sys.exit(1)
    r.close()
    ssh_client.execute_python_script("/home/chenzefeng/Documents/test/can_inject_test/main.py", f"{archecture} {cartype} {workflowId}") 
    ssh_client.close()

        


    


