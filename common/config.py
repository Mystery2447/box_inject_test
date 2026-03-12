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
API_TOKEN = "Bearer eyJraWQiOiJkMDVlMTU5NDJmODM0ZDEzODE0MDgxYzY4YzIxMWY0YiIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJ0ZW5hbnRfaWQiOjY4LCJzdWIiOiI0ODg5IiwiZGV2aWNlX2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJpc3MiOiJkcmF1dGgiLCJ0b2tlbl90eXBlIjoiQUNDRVNTIiwiY2xpZW50X2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJzaWQiOiI2ZGIzZTI4MC04NjVkLTRkMmItYTExMy0wYTJiY2E0ZjU4MDkiLCJhdWQiOiJkZWVwcm91dGUtbGRhcCIsImF1dGhfdGltZSI6MTc2OTY3NDc1NywidXNlclR5cGUiOiJJTlRFUk5BTCIsImV4cCI6MTc3MzM4MDQ0NiwiaWF0IjoxNzcyNzc1NjQ2LCJqdGkiOiIyOGJhNGY3OS02MzQ2LTQ2YjEtOGE2Zi1hMDgyNzExMDA2OGIiLCJlbWFpbCI6ImppZXllQGRlZXByb3V0ZS5haSIsInVzZXJuYW1lIjoiamlleWUifQ.ilxE5XnolIKCwTLaw2QeGDbRN6UxUWqcqoqa2e09W7o-Q1BBi_2rNrb2zirrOGpKu9EHRZPK7o0ManjjEC_866wGQ8bMZ-Ycx3Fk4MEN7Yf0LTM2FPPtfSbNO58AMTSYqjBn-Rcx0291NZNwqrTlTHHIE8dSWcrDhf8O73s7npvUnDE6ghvGf2wMJwhkptBLZUOZOd2d3W7Bx-0w-IqAG5j0EQjRe4sSyHrCX3ZsipqOfhrBadJf8PXfB0m_zbTck28fx9J9P0NS2T4if_JNnJD7ZTXQPejZ5LQYgrHnlhAPMVUMJk8QL0Kb1J_mNozahwTe3v_7-flqXxh7DcoFEg"

