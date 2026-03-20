import requests
import json


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


class FeishuSheetAPI:
    """飞书表格 API（读写数据）"""
    def __init__(self, spreadsheet_token=None, sheet_id=None):
        self.App_ID = "cli_a72719d632be901c"
        self.App_Secret = "MWxgknshTRR5pIAgXDdDmhRwmIQdMdbN"
        self.spreadsheet_token = spreadsheet_token
        self.sheet_id = sheet_id
        self.tenant_access_token = self.get_tenant_access_token()

    def get_tenant_access_token(self):
        """获取飞书租户令牌（用于 API 鉴权）"""
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
        
if __name__ =="__main__":
    robot = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/458b4208-1a5b-46c6-b52f-32ce501622a1")
    robot.send_text("jingcheng下午去人事办下手续。")