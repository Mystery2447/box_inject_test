from flash_mcu import flash_mcu
from flash_switch import flash_switch
import sys
import time
import serial.tools.list_ports
from common.relay import find_relay_com, Relay
from common.utils import get_guanzhaung_pack_info




if __name__ == "__main__":
    print("=== 全自动刷写工具 ===\n")
    print("input: python auto_flash.py <架构> <workflowID>")
    if(len(sys.argv) < 3):
        print("❌ 错误: 参数不足")
        print("usage: python auto_flash.py <架构> <workflowID>")
        print("example: python auto_flash.py THOR/ORINY/ORINX 3efe73e3-...")
        sys.exit(1)
    

    relay_port = find_relay_com()
    if not relay_port:
        print("❌ 错误: 未找到继电器设备")
        sys.exit(1)
    r = Relay(relay_port)
    print(f"✅ 继电器设备连接成功: {relay_port}")



    archecture = sys.argv[1].strip().lower()
    workflowId = sys.argv[2].strip()
    print(f"架构: {archecture}")
    print(f"workflowId: {workflowId}")
    pack_info = get_guanzhaung_pack_info(workflowId)

    r.ch_all_off()
    print("✅ 继电器全断开\n")
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
        r.close()
        sys.exit(1)
    if flag_switchb_en == True:
        print("正在执行 SWITCH-B 线刷流程...")
        r.ch1_off()  # 关闭通道1
        time.sleep(1)  # 等待继电器切换
        r.ch2_on()   # 打开通道2，连接到 SWITCH-B
        ret = flash_switch(archecture, pack_info.get('sourceSwitchB').get('uuid'))
        if ret:
            print("✅ SWITCH-B 刷写成功")
        else:
            print("❌ SWITCH-B 刷写失败，流程终止")
            r.close()
            sys.exit(1)

    
    print("正在执行 MCU 刷写流程...")
    ret = flash_mcu(archecture, pack_info.get('sourceMcu').get('uuid'))
    if ret:
        print("✅ MCU 刷写成功")
    else:
        print("❌ MCU 刷写失败，流程终止")
        r.close()
        sys.exit(1)

        


    


