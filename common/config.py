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
    "P03": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "P03_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "P03_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "P03_SOCProgrammerTools"),
    },
    "Thor": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "Thoru_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "Thoru_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "Thoru_SOCProgrammerTools"),
    },
    "C01": {
        "switch_dir": os.path.join(BASE_FLASH_DIR, "C01_SwitchProgrammerTools"),
        "mcu_dir": os.path.join(BASE_FLASH_DIR, "C01_MCUProgrammerTools"),
        "soc_dir": os.path.join(BASE_FLASH_DIR, "C01_SOCProgrammerTools"),
    }
}

# 3. API 配置 
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer eyJraWQiOiJkMDVlMTU5NDJmODM0ZDEzODE0MDgxYzY4YzIxMWY0YiIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJ0ZW5hbnRfaWQiOjY4LCJzdWIiOiI0ODg5IiwiZGV2aWNlX2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJpc3MiOiJkcmF1dGgiLCJ0b2tlbl90eXBlIjoiQUNDRVNTIiwiY2xpZW50X2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJzaWQiOiIzMjQxOWJmZC0wNmNlLTQyMDAtYTBjNS1iZjZjZGNmYjhhMmQiLCJhdWQiOiJkZWVwcm91dGUtbGRhcCIsImF1dGhfdGltZSI6MTc3MTg5ODI4MiwidXNlclR5cGUiOiJJTlRFUk5BTCIsImV4cCI6MTc3MzEyMzgzMiwiaWF0IjoxNzcyNTE5MDMyLCJqdGkiOiJkYzI0NDE3YS01NzNiLTQxNjEtYWM3ZS1kODYxOTNlZDUwNzciLCJlbWFpbCI6ImppZXllQGRlZXByb3V0ZS5haSIsInVzZXJuYW1lIjoiamlleWUifQ.RuEdMj5edTaDVKbc5c5Ah3TFDfbmBF5camRlAbi778fYPx5TbssRYS-5lTvWy1JIQ4xqR0aVfcHtXZy1tQLur8Ga5cR71enjyb6j0z-lq5raDqiIow4-_jz-Qt5Wi9sTm2QSmSM8EDlSNaiRwcpizzU8IYr6VmTVx_MK6GJdoNLNqtN7f8Cug9ThEZQg7halIF7IP9sKWLEMDzywxMh2FyDrPrIT53b3VWWwlCwqydZ0vbAA3JhuLwAHVfTPN72IcASZBRUli7FHhx2Ikv4ZIOPXsaWskr8gr6ku9-2VFJQR92XtZlCmjTyaXXJ6Jl8wjaSXfD4Mgf9pOavw939cGg"

