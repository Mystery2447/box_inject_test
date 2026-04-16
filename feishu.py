import requests
import json
import time

SPREADSHEET_TOKEN = "J6oEsu8NnhM9VotJu1jcObjznhf"

# ─── 表格结构常量（所有方法共用，不再重复定义）────────────────────────────────
TEST_ITEMS = [
    "MD5_MCU",
    "MD5_Switch",
    "MD5_SwitchB",
    "Serial_MCU version",
    "Serial_Switch version",
    "Serial_SwitchB version",
    "SOC version",
    "head ADS-METADATA",
    "tail ADS-METADATA",
    "GWM version (file)",
    "DEM status",
    "dr_info",
    "DOIP gwm_version",
    "DOIP gwm_software_infomation",
    "DOIP gwm_Calibration_version",
    "DEM restart status",
    "OTA result",
    "OTA后 GWM version",
    "OTA后 DEM status",
    "OTA后 dr_info",
]

FIELD_MAPPING = {
    "MD5_MCU":                        "mcu_md5",
    "MD5_Switch":                     "switch_md5",
    "MD5_SwitchB":                    "switchb_md5",
    "Serial_MCU version":             "mcu_version",
    "Serial_Switch version":          "switch_version",
    "Serial_SwitchB version":         "switchb_version",
    "SOC version":                    "soc_version",
    "head ADS-METADATA":              "driver_fullName",
    "tail ADS-METADATA":              "driver_gwmShortName",
    "GWM version (file)":             "gwm_version",
    "DEM status":                     "dem_status",
    "dr_info":                        "dr_info",
    "DOIP gwm_version":               "doip_gwm_version",
    "DOIP gwm_software_infomation":   "doip_gwm_software_infomation",
    "DOIP gwm_Calibration_version":   "doip_gwm_calibration_version",
    "DEM restart status":             "dem_restart",
    "OTA result":                     "ota_result",
    "OTA后 GWM version":              "ota_gwm_version",
    "OTA后 DEM status":               "ota_dem_status",
    "OTA后 dr_info":                  "ota_dr_info",
}

# 有期望值时参与 Pass/Fail 自动比对的测试项
_COMPARABLE = {
    "Serial_MCU version", "Serial_Switch version", "Serial_SwitchB version",
    "SOC version", "head ADS-METADATA", "tail ADS-METADATA",
    "GWM version (file)", "DOIP gwm_version",
}

# 颜色
_C_HEADER    = "#D0D0D0"   # 灰色（列表头）
_C_PASS      = "#B7E1CD"   # 绿（Pass）
_C_FAIL      = "#F4CCCC"   # 红（Fail）
_C_NA        = "#F5F5F5"   # 灰（无期望值 / 不参与比对）
_C_INFO      = "#EFEFEF"   # 浅灰（汇总信息行）
_C_ROW_ODD   = "#FFFFFF"

# 数据行起始行号（Row 1-4=汇总信息各一行，Row 5=列表头，Row 6+ = 数据）
_INFO_ROWS   = 4
_DATA_START  = 6


class FeishuRobot:
    """飞书机器人（文本/卡片消息发送）"""
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.headers = {"Content-Type": "application/json; charset=utf-8"}

    def send_text(self, content, at_all=False, at_users=None):
        """发送文本消息"""
        data = {
            "msg_type": "text",
            "content": {"text": content}
        }
        if at_all:
            data["content"]["text"] += " @所有人"
            data["at"] = {"is_at_all": True}
        elif at_users and isinstance(at_users, list):
            for user_id in at_users:
                data["content"]["text"] += f" <at user_id=\"{user_id}\"></at>"
            data["at"] = {"user_id": at_users}
        return self._send_request(data)

    def send_card(self, title, content, btn_text="查看详情", btn_url=None):
        """发送卡片消息（支持按钮链接）"""
        elements = [{"tag": "div", "text": {"tag": "lark_md", "content": content}}]
        if btn_url:
            elements.append({
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": btn_text},
                    "url": btn_url,
                    "type": "primary"
                }]
            })
        data = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": elements
            }
        }
        return self._send_request(data)

    def _send_request(self, data):
        try:
            response = requests.post(
                url=self.webhook_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            result = response.json()
            if result.get("code") == 0:
                print("飞书消息发送成功")
                return True
            print(f"飞书消息发送失败：{result.get('msg')}")
            return False
        except Exception as e:
            print(f"飞书请求出错：{str(e)}")
            return False


class FeishuReporter:
    """飞书表格报告器：新建 Sheet、写入模板、自动 Pass/Fail 着色"""

    def __init__(self, cartype="未知"):
        self.App_ID = "cli_a72719d632be901c"
        self.App_Secret = "MWxgknshTRR5pIAgXDdDmhRwmIQdMdbN"
        self.spreadsheet_token = SPREADSHEET_TOKEN
        self.cartype = cartype.upper()
        self.sheet_id = None
        self._expected_data = {}           # 缓存期望值，用于 Pass/Fail 比对
        self.tenant_access_token = self.get_tenant_access_token()

    # ─── 认证 ─────────────────────────────────────────────────────────────────

    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json; charset=utf-8"},
                data=json.dumps({"app_id": self.App_ID, "app_secret": self.App_Secret})
            )
            if resp.status_code == 200:
                token = resp.json().get("tenant_access_token")
                if token:
                    print("飞书租户令牌获取成功")
                    return token
            print(f"飞书令牌获取失败：{resp.text}")
            return ""
        except Exception as e:
            print(f"飞书令牌请求出错：{str(e)}")
            return ""

    def _auth_headers(self):
        return {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json",
        }

    def _check_token(self, op="操作"):
        if not self.tenant_access_token:
            print(f"❌ [Feishu] 无有效 Token，无法{op}")
            return False
        return True

    def _check_sheet(self, op="操作"):
        if not self.sheet_id:
            print(f"❌ [Feishu] sheet_id 未设置，无法{op}")
            return False
        return True

    # ─── Sheet 管理 ───────────────────────────────────────────────────────────

    def create_sheet(self, title):
        if not self._check_token("创建工作表"):
            return None
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/sheets_batch_update"
        payload = {"requests": [{"addSheet": {"properties": {"title": title, "index": 0}}}]}
        try:
            resp = requests.post(url, headers=self._auth_headers(), json=payload)
            res = resp.json()
            if res.get("code") == 0:
                new_id = res["data"]["replies"][0]["addSheet"]["properties"]["sheetId"]
                print(f"✅ [Feishu] 工作表 '{title}' 创建成功，sheetId: {new_id}")
                return new_id
            print(f"❌ [Feishu] 创建工作表失败: {res}")
            return None
        except Exception as e:
            print(f"❌ [Feishu] 创建工作表异常: {e}")
            return None

    # ─── 批量读写 ─────────────────────────────────────────────────────────────

    def batch_update(self, value_ranges):
        if not self._check_token("写入"):
            return False
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update"
        try:
            resp = requests.post(url, headers=self._auth_headers(), json={"valueRanges": value_ranges})
            res = resp.json()
            if res.get("code") == 0:
                print("✅ [Feishu] 批量写入成功")
                return True
            print(f"❌ [Feishu] 批量写入失败: {res}")
            return False
        except Exception as e:
            print(f"❌ [Feishu] 批量写入异常: {e}")
            return False

    def write_data(self, data_range, data_value):
        if not self._check_token("写入"):
            return -1
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values"
        if isinstance(data_value, str):
            values = [[data_value]]
        elif isinstance(data_value, list):
            values = data_value if (data_value and isinstance(data_value[0], list)) else [data_value]
        else:
            values = [[str(data_value)]]
        body = {"valueRange": {"range": f"{self.sheet_id}!{data_range}", "values": values}}
        try:
            resp = requests.put(url, headers=self._auth_headers(), json=body)
            if resp.status_code == 200 and resp.json().get("code") == 0:
                return 0
            print(f"表格写入失败：{resp.text}")
            return -1
        except Exception as e:
            print(f"表格写入请求出错：{str(e)}")
            return -1

    def read_data(self, data_range):
        if not self._check_token("读取"):
            return []
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values/{self.sheet_id}!{data_range}"
        try:
            resp = requests.get(url, headers=self._auth_headers())
            if resp.status_code == 200 and resp.json().get("code") == 0:
                return resp.json().get("data", {}).get("valueRange", {}).get("values", [])
            print(f"表格读取失败：{resp.text}")
            return []
        except Exception as e:
            print(f"表格读取请求出错：{str(e)}")
            return []

    # ─── 格式化 ───────────────────────────────────────────────────────────────

    def merge_cells(self, cell_range: str):
        """合并单元格（MERGE_ALL：将范围内所有单元格合并为一个）"""
        if not self._check_token("合并单元格"):
            return False
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/merge_cells"
        try:
            resp = requests.post(url, headers=self._auth_headers(), json={
                "range": f"{self.sheet_id}!{cell_range}",
                "mergeType": "MERGE_ALL",
            })
            if resp.json().get("code") == 0:
                print(f"✅ 合并单元格: {cell_range}")
                return True
            print(f"❌ 合并失败: {resp.json()}")
            return False
        except Exception as e:
            print(f"❌ 合并异常: {e}")
            return False

    def set_column_width(self, start_index, end_index, width):
        """
        设置列宽（0-based，end_index 为开区间）
        例：列 A → start=0, end=1；列 B → start=1, end=2
        """
        if not self._check_token("设置列宽"):
            return False
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/dimension_range"
        payload = {
            "dimension": {
                "sheetId": self.sheet_id,
                "majorDimension": "COLUMNS",
                "startIndex": start_index,
                "endIndex": end_index,
            },
            "dimensionProperties": {"fixedSize": width, "visible": True},
        }
        try:
            resp = requests.put(url, headers=self._auth_headers(), json=payload)
            if resp.json().get("code") == 0:
                print(f"✅ [Feishu] 列宽设置成功 ({start_index}~{end_index}: {width}px)")
                return True
            print(f"❌ [Feishu] 列宽设置失败: {resp.json()}")
            return False
        except Exception as e:
            print(f"❌ [Feishu] 列宽设置异常: {e}")
            return False

    def format_guanzhuang_sheet(self, row_count: int):
        """
        格式化表格。
        关键：每个 style 条目都显式带 FULL_BORDER，防止后续覆盖时丢失边框。
        不使用 OUTER_BORDER（它会清除已设置的内部边框）。
        """
        if not self._check_token("格式化"):
            return False
        url  = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/styles_batch_update"
        sid  = self.sheet_id
        hrow = _DATA_START - 1                   # 列表头行号 = 5
        last = _DATA_START + row_count - 1       # 最后数据行行号 = 25

        _B = {"borderType": "FULL_BORDER", "borderColor": "#000000"}   # 统一黑色边框

        style_data = [
            {   # ① 基础：整个表格所有单元格黑色边框 + 白色背景
                "ranges": [f"{sid}!A1:E{last}"],
                "style": {**_B, "backColor": "#FFFFFF", "hAlign": 1, "vAlign": 1}
            },
            {   # ② 汇总信息 A 列（标签）：浅灰 + 加粗 + 左对齐
                "ranges": [f"{sid}!A1:A{_INFO_ROWS}"],
                "style": {**_B, "backColor": _C_INFO, "hAlign": 0, "vAlign": 1,
                          "font": {"bold": True}}
            },
            {   # ③ 汇总信息值（合并单元格锚点 B 列）：浅灰 + 加粗 + 左对齐
                "ranges": [f"{sid}!B1:B{_INFO_ROWS}"],
                "style": {**_B, "backColor": _C_INFO, "hAlign": 0, "vAlign": 1,
                          "font": {"bold": True}}
            },
            {   # ④ 列表头行：灰色背景 + 加粗 + 居中
                "ranges": [f"{sid}!A{hrow}:E{hrow}"],
                "style": {**_B, "backColor": _C_HEADER, "hAlign": 1, "vAlign": 1,
                          "font": {"bold": True}}
            },
            {   # ⑤ 数据行：白色背景 + 居中
                "ranges": [f"{sid}!A{_DATA_START}:E{last}"],
                "style": {**_B, "backColor": "#FFFFFF", "hAlign": 1, "vAlign": 1}
            },
        ]

        try:
            resp = requests.put(url, headers=self._auth_headers(), json={"data": style_data})
            if resp.status_code == 200 and resp.json().get("code") == 0:
                print("✅ 表格格式化完成")
                return True
            print(f"❌ 表格格式化失败: {resp.text}")
            return False
        except Exception as e:
            print(f"❌ 表格格式化异常: {e}")
            return False

    def _color_result_column(self, results: list):
        """
        根据 Pass/Fail/NA 批量着色 Test_result 列（E 列）。
        results: 与 TEST_ITEMS 等长的字符串列表，值为 "Pass"/"Fail"/"—"
        """
        if not self._check_token("着色"):
            return
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/styles_batch_update"

        color_map = {"Pass": _C_PASS, "Fail": _C_FAIL}
        style_data = []
        for idx, result in enumerate(results):
            row   = idx + _DATA_START - 1   # 数据从 _DATA_START 行开始
            color = color_map.get(result, _C_NA)
            style_data.append({
                "ranges": [f"{self.sheet_id}!E{row}:E{row}"],
                "style": {
                    "backColor": color,
                    "hAlign": 1, "vAlign": 1,
                    "font": {"bold": result in ("Pass", "Fail")},
                    "borderType": "FULL_BORDER", "borderColor": "#CCCCCC",
                }
            })

        try:
            resp = requests.put(url, headers=self._auth_headers(), json={"data": style_data})
            if resp.status_code == 200 and resp.json().get("code") == 0:
                print("✅ Pass/Fail 着色完成")
            else:
                print(f"❌ 着色失败: {resp.text}")
        except Exception as e:
            print(f"❌ 着色异常: {e}")

    # ─── 报告模板 ─────────────────────────────────────────────────────────────

    def create_guanzhuang_template(self, oemversion: str, workflow_id: str = None):
        """
        新建工作表并写入模板框架。
        Row 1: 汇总信息（车型 / 工作流ID / 测试人员 / 测试时间）
        Row 2: 列表头
        Row 3+: 测试项
        """
        oem_suffix = f"-{oemversion}" if oemversion else ""
        now = time.localtime()
        sheet_title = (
            f"{now.tm_hour}:{now.tm_min:02d}-"
            f"{now.tm_year}.{now.tm_mon}.{now.tm_mday}-"
            f"{self.cartype}{oem_suffix}-罐装包测试报告"
        )
        print(f"创建工作表: {sheet_title}")

        new_sheet_id = self.create_sheet(sheet_title)
        if not new_sheet_id:
            print("❌ 创建工作表失败，终止写入")
            return False
        self.sheet_id = new_sheet_id

        test_time = f"{now.tm_year}.{now.tm_mon}.{now.tm_mday} {now.tm_hour}:{now.tm_min:02d}"
        wf_id     = workflow_id if workflow_id else "—"

        # Row 1-4: 汇总信息（每条独占一行，A=标签 B=值）
        # Row 5:   列表头
        # Row 6+:  测试项
        value_ranges = [
            {"range": f"{new_sheet_id}!A1:E1", "values": [["车型",     self.cartype,       "", "", ""]]},
            {"range": f"{new_sheet_id}!A2:E2", "values": [["工作流ID", wf_id,              "", "", ""]]},
            {"range": f"{new_sheet_id}!A3:E3", "values": [["测试人员", "自动化测试",        "", "", ""]]},
            {"range": f"{new_sheet_id}!A4:E4", "values": [["测试时间", test_time,           "", "", ""]]},
            {"range": f"{new_sheet_id}!A5:E5", "values": [["Case_id", "Test_item", "Expected_result", "Test_data", "Test_result"]]},
        ]
        for idx, item in enumerate(TEST_ITEMS, start=1):
            row = idx + _DATA_START - 1
            value_ranges.append({
                "range": f"{new_sheet_id}!A{row}:E{row}",
                "values": [[idx, item, "", "", ""]]
            })

        if not self.batch_update(value_ranges):
            print("❌ 模板写入失败")
            return False

        # 合并汇总信息行的值单元格（B:E 合并为一个单元格）
        for row in range(1, _INFO_ROWS + 1):
            self.merge_cells(f"B{row}:E{row}")

        self.format_guanzhuang_sheet(len(TEST_ITEMS))

        # 列宽（1-based 开区间）：A=60, B=200, C=320, D=320, E=100
        for start, end, width in [(1, 2, 60), (2, 3, 200), (3, 4, 320), (4, 5, 320), (5, 6, 100)]:
            self.set_column_width(start, end, width)

        print(f"✅ 表格模板创建完成: {sheet_title}")
        return True

    def update_expect_result(self, data: dict):
        """
        写入 Expected_result 列（C 列）并缓存数据供后续 Pass/Fail 比对。
        """
        if not self._check_sheet("写入期望值"):
            return False

        self._expected_data = data   # 缓存，update_test_result 时比对用

        values = []
        for item in TEST_ITEMS:
            key = FIELD_MAPPING.get(item)
            values.append([str(data.get(key, "")) if data.get(key) is not None else ""])

        payload = {"valueRanges": [{
            "range": f"{self.sheet_id}!C{_DATA_START}:C{len(TEST_ITEMS)+_DATA_START-1}",
            "values": values,
        }]}
        resp = requests.post(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update",
            headers=self._auth_headers(), json=payload
        )
        if resp.status_code == 200 and resp.json().get("code") == 0:
            print("✅ 已写入 Expected_result 列")
            return True
        print(f"❌ 写入 Expected_result 列失败: {resp.text}")
        return False

    def update_test_result(self, data: dict):
        """
        写入 Test_data 列（D 列）并自动计算 Test_result 列（E 列）：
        - 在 _COMPARABLE 中且期望/实际均有值：相同→Pass，不同→Fail
        - 其余项（DEM、dr_info 等）：显示 "—"
        - OTA result 特殊处理：含 "success"→Pass，否则→Fail
        """
        if not self._check_sheet("写入测试结果"):
            return False

        actual_values  = []
        result_values  = []
        result_labels  = []   # 用于着色

        for item in TEST_ITEMS:
            key    = FIELD_MAPPING.get(item)
            actual = data.get(key)
            actual_str = str(actual) if actual is not None else ""

            expected_key = FIELD_MAPPING.get(item)
            expected     = self._expected_data.get(expected_key)
            expected_str = str(expected) if expected is not None else ""

            actual_values.append([actual_str])

            # ── 计算 Pass/Fail ──────────────────────────────────────────────
            if item == "OTA result":
                if actual_str and "success" in actual_str.lower():
                    label = "Pass"
                elif actual_str:
                    label = "Fail"
                else:
                    label = "—"

            elif item in _COMPARABLE and expected_str and actual_str:
                label = "Pass" if actual_str == expected_str else "Fail"

            else:
                label = "—"

            result_values.append([label])
            result_labels.append(label)

        # 一次性写入 D 列（Test_data）和 E 列（Test_result）
        n    = len(TEST_ITEMS)
        end  = n + _DATA_START - 1
        payload = {"valueRanges": [
            {"range": f"{self.sheet_id}!D{_DATA_START}:D{end}", "values": actual_values},
            {"range": f"{self.sheet_id}!E{_DATA_START}:E{end}", "values": result_values},
        ]}
        resp = requests.post(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update",
            headers=self._auth_headers(), json=payload
        )
        if resp.status_code == 200 and resp.json().get("code") == 0:
            print("✅ 已更新 Test_data 和 Test_result 列")
            self._color_result_column(result_labels)   # 着色
            return True
        print(f"❌ 更新测试结果失败: {resp.text}")
        return False


# ─── 单元测试入口 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = {
        "mcu_md5": "mcu_md5_abc",
        "switch_md5": "switch_md5_abc",
        "switchb_md5": "switchb_md5_abc",
        "mcu_version": "ADC4.0_MCU_R1.2_260101_1A2B3C",
        "switch_version": "ADC4.0_S-5192A_260101_4D5E6F",
        "switchb_version": "ADC4.0_S-5192B_260101_7A8B9C",
        "soc_version": "soc_v2.3.1",
        "dem_status": "active (running)",
        "dem_restart": "active (running)",
        "driver_fullName": "ADS_v3.2.1_20260101",
        "driver_gwmShortName": "GWM_SHORT_v3.2",
        "gwm_version": "GWM_v3.2.1",
        "dr_info": '{"mcu": "1.2", "switch": "1.3"}',
        "doip_gwm_version": "GWM_v3.2.1",
        "doip_gwm_software_infomation": "SW_INFO_v1.0",
        "doip_gwm_calibration_version": "CAL_v1.0",
        "ota_result": "success",
        "ota_gwm_version": "GWM_v3.3.0",
        "ota_dem_status": "active (running)",
        "ota_dr_info": '{"mcu": "1.3", "switch": "1.4"}',
    }
    reporter = FeishuReporter(cartype="THOR")
    reporter.create_guanzhuang_template("008", workflow_id="86ebf5be-f311-4a2f-9df2-dbc0617cffc4")
    reporter.update_expect_result(demo)
    reporter.update_test_result(demo)
