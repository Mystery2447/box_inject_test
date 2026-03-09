import sys
import time
import json
import inject_key
from ssh_client import SshClient
from doip import DoipClient
from my_serial import Serial_device
from feishu import FeishuRobot, FeishuSheetAPI


def serial_check():
    try:
        mcu_serial = Serial_device()    #ttyUSB0
        mcu_serial.send_data("poweron\r\n") #just in case
        mcu_version =  mcu_serial.check_mcu_version()
        if mcu_version ==-1:
            print("[WARNNING]:could not find mcu version")
        switch_version = mcu_serial.check_switch_version()
        if switch_version ==-1:
            print("[WARNNING]:could not find switch version")
    except FileNotFoundError:
        ero_msg = f"could not find ttyUSB0"
        print(f"[ERROR]{ero_msg}")
        exit(-1)
    except UnboundLocalError:
        ero_msg = f"could not find MCU/SWITCH version"
        print(f"[ERROR]{ero_msg}")
        exit(-1)
    finally:
        mcu_serial.close()
    return mcu_version,switch_version


def ssh_check(car_type='ORINX'):
    ssh_test = SshClient(Architecture=car_type)
    test_info = ssh_test.test()
    return test_info

def inject_key_check(car_type = 'C01',Architecture = 'ORINX'):
    if Architecture == 'ORINX':
        return None
    else:
        inject_key.set_network("enx207bd51a13cc")
        inject_key.inject_other_key()
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

def AFTER_OTA_CHECK(car_type='ORINX'):
    ssh_test = SshClient(Architecture=car_type)
    test_info = ssh_test.after_test()
    return test_info



if __name__ =='__main__':
    print("first para is architect ,second is car_type")
    if len(sys.argv)>2:
        car_TEST = sys.argv[1]  #orin平台
        car_type = sys.argv[2]  #具体车型
    else:
        car_TEST = 'ORINX'
        car_type = 'C01'
    feishu_test = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/86f13735-aa8e-4dc1-aa6a-258177111a1e")
    mcu_version,switch_version = serial_check()
    inject_key_check(car_type=car_type,Architecture=car_TEST)

    doip_guangzhuang_version = doip_check(car_type)
    test_info = ssh_check(car_type=car_TEST)

    feishu_test.send_text(
    content=f"--------------------- can inject test ---------------------\r\n\
\r\n\
--------------------- 1. serial read - MCU ---------------------\r\n\
{mcu_version}  \r\n\
\r\n\
--------------------- 2. serial read - switch ---------------------\r\n\
{switch_version} \r\n\
\r\n\
--------------------- 3. head ADS-METADATA ---------------------\r\n\
{test_info['head-ADS.METADATA']}\r\n\
\r\n\
--------------------- 4. tail ADS-METADATA ---------------------\r\n\
{test_info['tail-ADS.METADATA']}\r\n\
\r\n\
--------------------- 5. SOC version ---------------------\r\n\
{test_info['SOC_version']} \r\n\
\r\n\
--------------------- 6. file_gwm_version ---------------------\r\n\
GWM 版本：{test_info['file_gwm_version']}\r\n\
--------------------- 7. DEM status ---------------------\r\n\
{test_info['dem_status']}  \r\n\
\r\n\
--------------------- 8. read dr_info ---------------------\r\n\
{test_info['dr_info']}\r\n\
\r\n\
--------------------- 9.DOIP read version ---------------------\r\n\
 gwm_version:{doip_guangzhuang_version['gwm_version']}\r\n\
 gwm_software_infomation:{doip_guangzhuang_version['gwm_software_infomation']}\r\n\
 gwm_Calibration_version:{doip_guangzhuang_version['gwm_Calibration_version']}\r\n\
# --------------------- 10. DEM restart status ---------------------\r\n\
{test_info['dem_restart']} \r\n\
\r\n\
start to ota test..."
)
    for i in range(80,0,-1):
        print(f"dem init cnt:{i}s  ",end='\r')
        time.sleep(1)
  
    ret = doip_OTA(car_TEST)
    if ret == 'success OTA':
        feishu_test.send_text(ret)
        ret = AFTER_OTA_CHECK(car_TEST)
        feishu_test.send_text(f"--------------------- 1. file_gwm_version ---------------------\r\n\
GWM 版本：{ret['file_gwm_version']}\r\n\
--------------------- 2. DEM status ---------------------\r\n\
{ret['dem_status']}  \r\n\
\r\n\
--------------------- 3. read dr_info ---------------------\r\n\
{ret['dr_info']}\r\n\
\r\n:")
    elif ret == 'not start OTA.wrong archi!!!':
        feishu_test.send_text(ret)
    else:
        feishu_test.send_text(ret)
    # ssh_test = SshClient(Architecture=car_TEST)
    # doip_test = DoipClient()
    # doip_test.car_type = car_type
    # doip_test.client_setup()
    # doip_test.route_active()
    # ret = doip_test.write_F1B1_car_config_VIN()
    # doip_test.sock_close()
    # if "failed" in ret:
    #     feishu_test.send_text("F1B1 inject fail,plz manually confirm")
    # else:
    #     feishu_test.send_text("F1B1 inject success")
    #     time.sleep(40)
    #     doip_test.client_setup()
    #     doip_test.route_active()
    #     doip_guangzhuang_version = doip_test.check_guanzhuang_version()
    #     doip_test.sock_close()
    #     test_info = ssh_test.test()
#         feishu_test.send_text(
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



    ...
