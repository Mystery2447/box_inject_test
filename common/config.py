# ================= 全局配置 =================

# 1. 串口配置 (MCU Console)
MCU_SERIAL_PORT = "COM23"          
SOC_SERAL_PORT = "COM16"          
MCU_BAUDRATE = 115200             
SERIAL_TIMEOUT = 3.0              

# 2. 车型与路径配置
CAR_CONFIG = {
    "P03": {
        "switch_dir": r"C:\Users\jieye\Desktop\P03_SwitchProgrammerTools",
        "mcu_dir": r"C:\Users\jieye\Desktop\P03_MCUProgrammerTools",
        "soc_dir": r"C:\Users\jieye\Desktop\P03_SOCProgrammerTools",
    },
    "Thor": {
        "switch_dir": r"C:\Users\jieye\Desktop\Thoru_SwitchProgrammerTools",
        "mcu_dir": r"C:\Users\jieye\Desktop\Thoru_MCUProgrammerTools",
        "soc_dir": r"C:\Users\jieye\Desktop\Thoru_SOCProgrammerTools",
    },
    "C01": {
        "switch_dir": r"C:\Users\jieye\Desktop\C01_SwitchProgrammerTools",
        "mcu_dir": r"C:\Users\jieye\Desktop\C01_MCUProgrammerTools",
        "soc_dir": r"C:\Users\jieye\Desktop\C01_SOCProgrammerTools",
    }
}

# 3. API 配置 
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer eyJraWQiOiJkMDVlMTU5NDJmODM0ZDEzODE0MDgxYzY4YzIxMWY0YiIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJ0ZW5hbnRfaWQiOjY4LCJzdWIiOiI0ODg5IiwiZGV2aWNlX2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJpc3MiOiJkcmF1dGgiLCJ0b2tlbl90eXBlIjoiQUNDRVNTIiwiY2xpZW50X2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJzaWQiOiI5NmNkNzhiZS02OTYwLTQzMmUtYWE4NS01NzYwOTBiOWNiMTgiLCJhdWQiOiJkZWVwcm91dGUtbGRhcCIsImF1dGhfdGltZSI6MTc2OTQyNDAxOCwidXNlclR5cGUiOiJJTlRFUk5BTCIsImV4cCI6MTc3MDAyODgxOCwiaWF0IjoxNzY5NDI0MDE4LCJqdGkiOiJkMGI5M2Y1OS04ZTA3LTRlZjEtOWNlNS02ZjA1YTA2OTkzNmMiLCJlbWFpbCI6ImppZXllQGRlZXByb3V0ZS5haSIsInVzZXJuYW1lIjoiamlleWUifQ.j3qmPbwSYh3OMb0HmAPVJkm8JxBWRiBV3zbxEst27wUoMAuGyzZgF-3CS9X2wGUqwp3kGDd0sU4xQuiqHb2hM5-sqVF3UI_26934LHRujqADLIrVgHp6AmDYhNQbOi_TkjJhz8itj94exyLjY7liboitkvRy3utXDJ6JKx5xl5MzZ40hOWiiBFO-bdKySj4EgshIOEqMvodGm71AqNHpYiQxP3E05-zfS5Cnd7Cg3cgGdXPcPClWN9HyzMVItXqTCEjLpQoQcgZGVgv7OdUSFj6mAbUGHIrMGh3T_btKZRX3_PPR6NnN1HUFjZn_XgaVk1AghiyV5UQQ-RVfAObISw"

