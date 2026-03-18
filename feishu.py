import requests
import json
import time

# 飞书多维表格 spreadsheet_token，需替换为你的实际表格 ID
SPREADSHEET_TOKEN = "J6oEsu8NnhM9VotJu1jcObjznhf"


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

        # 处理 @ 逻辑
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
        """通用请求发送方法"""
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
            else:
                print(f"飞书消息发送失败：{result.get('msg')}")
                return False
        except Exception as e:
            print(f"飞书请求出错：{str(e)}")
            return False


class FeishuReporter:
    """
    飞书表格报告器
    支持：获取 Token、新建工作表、批量写入数据
    """
    def __init__(self, spreadsheet_token):
        self.App_ID = "cli_a72719d632be901c"
        self.App_Secret = "MWxgknshTRR5pIAgXDdDmhRwmIQdMdbN"
        self.spreadsheet_token = spreadsheet_token
        self.tenant_access_token = self.get_tenant_access_token()

    def get_tenant_access_token(self):
        """获取飞书租户令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        body = {"app_id": self.App_ID, "app_secret": self.App_Secret}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            if response.status_code == 200:
                token = response.json().get("tenant_access_token")
                if token:
                    print("飞书租户令牌获取成功")
                    return token
            print(f"飞书令牌获取失败：{response.text}")
            return ""
        except Exception as e:
            print(f"飞书令牌请求出错：{str(e)}")
            return ""

    def write_data(self, data_range, data_value):
        """写入数据到表格（支持字符串、列表）"""
        if not self.tenant_access_token:
            print("[ERROR] 无有效租户令牌，无法写入表格")
            return -1

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # 格式化数据为二维数组（飞书表格要求格式）
        if isinstance(data_value, str):
            values = [[data_value]]
        elif isinstance(data_value, list):
            values = data_value if (data_value and isinstance(data_value[0], list)) else [data_value]
        else:
            values = [[str(data_value)]]

        body = {
            "valueRange": {
                "range": f"{self.sheet_id}!{data_range}",
                "values": values
            }
        }

        try:
            response = requests.put(url, headers=headers, json=body)
            if response.status_code == 200 and response.json().get("code") == 0:
                print(f"表格数据写入成功（范围：{data_range}）")
                return 0
            print(f"表格写入失败：{response.text}")
            return -1
        except Exception as e:
            print(f"表格写入请求出错：{str(e)}")
            return -1

    def read_data(self, data_range):
        """从表格读取数据"""
        if not self.tenant_access_token:
            print("[ERROR] 无有效租户令牌，无法读取表格")
            return []

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values/{self.sheet_id}!{data_range}"
        headers = {"Authorization": f"Bearer {self.tenant_access_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get("code") == 0:
                values = response.json().get("data", {}).get("valueRange", {}).get("values", [])
                print(f"表格数据读取成功（范围：{data_range}）")
                return values
            print(f"表格读取失败：{response.text}")
            return []
        except Exception as e:
            print(f"表格读取请求出错：{str(e)}")
            return []

    def create_sheet(self, title):
        """
        新建一个工作表
        :param title: 工作表名称，如 "2026.3.17罐装包测试结果"
        :return: 新建工作表的 sheet_id，失败返回 None
        """
        if not self.tenant_access_token:
            print("❌ [Feishu] 无有效 Token，无法创建工作表")
            return None

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/sheets_batch_update"

        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "index": 0
                        }
                    }
                }
            ]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload)
            res_json = resp.json()

            if res_json.get("code") == 0:
                new_sheet_id = res_json["data"]["replies"][0]["addSheet"]["properties"]["sheetId"]
                print(f"✅ [Feishu] 工作表 '{title}' 创建成功，sheetId: {new_sheet_id}")
                return new_sheet_id
            else:
                print(f"❌ [Feishu] 创建工作表失败: {res_json}")
                return None
        except Exception as e:
            print(f"❌ [Feishu] 创建工作表异常: {e}")
            return None

    def batch_update(self, value_ranges):
        """批量更新多个范围的数据"""
        if not self.tenant_access_token:
            print("❌ [Feishu] 无有效 Token，无法写入")
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values_batch_update"

        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "valueRanges": value_ranges
        }

        try:
            resp = requests.post(url, headers=headers, json=payload)
            res_json = resp.json()

            if res_json.get("code") == 0:
                print(f"✅ [Feishu] 测试数据批量写入成功")
                return True
            else:
                print(f"❌ [Feishu] 写入失败: {res_json}")
                return False
        except Exception as e:
            print(f"❌ [Feishu] 请求异常: {e}")
            return False


def report_guanzhuang_result(version_data, car_type="未知"):
    """
    新建一个以当前日期+车型命名的工作表，写入模板和测试数据

    :param version_data: dict, 包含版本信息
        {
            "mcu_version": "xxx",
            "switch_version": "xxx",
            "soc_version": "xxx"
        }
    :param car_type: str, 通过 F1B1 配置字比对得出的车型名称
    """
    reporter = FeishuReporter(SPREADSHEET_TOKEN)

    # 1. 生成工作表名称：如 "2026.3.17-DE09-罐装包测试报告"
    now = time.localtime()
    sheet_title = f"{now.tm_year}.{now.tm_mon}.{now.tm_mday}-{car_type}-罐装包测试报告"
    print(f"准备创建工作表: {sheet_title}")

    # 2. 新建工作表
    new_sheet_id = reporter.create_sheet(sheet_title)
    if not new_sheet_id:
        print("❌ 创建工作表失败，终止写入")
        return False

    # 3. 准备写入数据
    header_row = {
        "range": f"{new_sheet_id}!A1:E1",
        "values": [["Case_id", "Test_item", "Expected_result", "Test_data", "Test_result"]]
    }

    mcu_version = version_data.get("mcu_version", "")
    mcu_row = {
        "range": f"{new_sheet_id}!A2:E2",
        "values": [[
            1,
            "Serial_MCU version",
            "",
            mcu_version,
            "Pass" if mcu_version else "Fail"
        ]]
    }

    switch_version = version_data.get("switch_version", "")
    switch_row = {
        "range": f"{new_sheet_id}!A3:E3",
        "values": [[
            2,
            "Serial_Switch version",
            "",
            switch_version,
            "Pass" if switch_version else "Fail"
        ]]
    }

    soc_version = version_data.get("soc_version", "")
    soc_row = {
        "range": f"{new_sheet_id}!A4:E4",
        "values": [[
            3,
            "SOC version",
            "",
            soc_version,
            "Pass" if soc_version else "Fail"
        ]]
    }

    # 4. 批量写入（表头 + 3行数据，一次搞定）
    updates = [header_row, mcu_row, switch_row, soc_row]
    return reporter.batch_update(updates)


if __name__ == "__main__":
    # 创建工作表并写入测试数据（不发送机器人消息）
    # ===================== 模拟测试数据（平台: thor） =====================
    car_platform = "thor"

    mock_data = {
        "mcu_version": "GWM-THORU-SHARE-MCU-R6-26020601-B1",
        "switch_version": "DSV_SWITCH_ADC3.0_S_260107",
        "soc_version": "GWM-THORU-SHARE-SOC-R6-26012902"
    }
    report_guanzhuang_result(mock_data, car_type=car_platform)

    # ===================== 真实数据获取方式 (对接 main.py) =====================
    # car_platform = sys.argv[1]  # 运行时传入平台名称，如 python feishu2.py thor
    #
    # from main import serial_check, ssh_check
    # mcu_version, switch_version = serial_check()
    # test_info = ssh_check(car_type=car_platform.upper())
    #
    # real_data = {
    #     "mcu_version": mcu_version,
    #     "switch_version": switch_version,
    #     "soc_version": test_info['SOC_version']
    # }
    # report_guanzhuang_result(real_data, car_type=car_platform)

    # 以下为「发送飞书机器人消息」示例，不执行创建工作表时勿取消注释
    # robot = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/xxx")
    # robot.send_text("xxx")