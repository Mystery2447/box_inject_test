import os

# ================= 全局配置 =================

# 基础路径配置
BASE_FLASH_DIR = os.path.join(os.getcwd(), "flash_dir")

# 1. 串口配置 
MCU_SERIAL_PORT = "COM16"          
# SOC_SERAL_PORT = "COM16"          
MCU_BAUDRATE = 115200             
SERIAL_TIMEOUT = 3.0              

# 2. 车型与路径配置
CAR_CONFIG = {
    "oriny": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "P03_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "P03_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "P03_SOCProgrammerTools"),
    },
    "thor": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "Thoru_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "Thoru_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "Thoru_SOCProgrammerTools"),
    },
    "orinx": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "C01_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "C01_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "C01_SOCProgrammerTools"),
    }
}

# 3. API 配置 
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer adas-farm_77868_+ae2dmmu48degsjfayynp2n9o5ca3bbr"

