import requests
import os
import sys
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer eyJraWQiOiJkMDVlMTU5NDJmODM0ZDEzODE0MDgxYzY4YzIxMWY0YiIsInR5cCI6IkpXVCIsImFsZyI6IlJTMjU2In0.eyJ0ZW5hbnRfaWQiOjY4LCJzdWIiOiI0ODg5IiwiZGV2aWNlX2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJpc3MiOiJkcmF1dGgiLCJ0b2tlbl90eXBlIjoiQUNDRVNTIiwiY2xpZW50X2lkIjoiZGVlcHJvdXRlLWxkYXAiLCJzaWQiOiIzMjQxOWJmZC0wNmNlLTQyMDAtYTBjNS1iZjZjZGNmYjhhMmQiLCJhdWQiOiJkZWVwcm91dGUtbGRhcCIsImF1dGhfdGltZSI6MTc3MTg5ODI4MiwidXNlclR5cGUiOiJJTlRFUk5BTCIsImV4cCI6MTc3MzEyMzgzMiwiaWF0IjoxNzcyNTE5MDMyLCJqdGkiOiJkYzI0NDE3YS01NzNiLTQxNjEtYWM3ZS1kODYxOTNlZDUwNzciLCJlbWFpbCI6ImppZXllQGRlZXByb3V0ZS5haSIsInVzZXJuYW1lIjoiamlleWUifQ.RuEdMj5edTaDVKbc5c5Ah3TFDfbmBF5camRlAbi778fYPx5TbssRYS-5lTvWy1JIQ4xqR0aVfcHtXZy1tQLur8Ga5cR71enjyb6j0z-lq5raDqiIow4-_jz-Qt5Wi9sTm2QSmSM8EDlSNaiRwcpizzU8IYr6VmTVx_MK6GJdoNLNqtN7f8Cug9ThEZQg7halIF7IP9sKWLEMDzywxMh2FyDrPrIT53b3VWWwlCwqydZ0vbAA3JhuLwAHVfTPN72IcASZBRUli7FHhx2Ikv4ZIOPXsaWskr8gr6ku9-2VFJQR92XtZlCmjTyaXXJ6Jl8wjaSXfD4Mgf9pOavw939cGg"
DOWNLOAD_PATH = "/tmp/diff_pack_download"

class DiffPackClient:
    def __init__(self,Architecture=None,workflow_id=None):
        self.architecture = Architecture
        if self.architecture is None:
            self.ssh_password = "#7F7d8or"
        elif self.architecture == 'ORINX':
            self.ssh_password = "W8k3L2@m;"
        elif self.architecture == "ORINY":
            self.ssh_password = "#7F7d8or"
        elif self.architecture == "THOR":
            self.ssh_password = "G7#kL2@m"
        else:
            print("[ERROR]:wrong architect!\n"
                  "pls select the architect below:\n"
                  "ORINX\ORINY\THOR\n")
            raise ValueError(f"unkonw architect: {Architecture}")
        self.download_path = DOWNLOAD_PATH
        self.workflow_id = workflow_id
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def get_diffpack_url(self):
        diffpack_id = self.get_diffpack_id()
        if diffpack_id:
            headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            resp = requests.get(f"{API_BASE_URL}/api/v1/workflow/diff-tasks/{diffpack_id}", headers=headers, verify=False, data=None)
            resp.raise_for_status()
            raw_data = resp.json().get('data', {})
            # print(f"原始 API 响应数据: {raw_data}") 

            return raw_data.get('downloadUrl')
        return None

    def get_diffpack_id(self):
        headers  = headers = {
            'Authorization': API_TOKEN,
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        workflow_data = resp.json().get('data', {})
        diff_status = workflow_data.get('diffMsg')
        if(diff_status is not None):
            diffpack_id = workflow_data.get('diffId')
            print(f"diffpack_id: {diffpack_id}")
            return  f"{diffpack_id}"
        print(f"diff状态: {diff_status}")
        return None
    def download_diffpack(self, url):
        os.system(f"wget -O {self.download_path}/a.zip '{url}' --no-check-certificate")

    def scp_diffpack(self):
        # Implementation for SCP diffpack
        os.system(f"sshpass -p '{self.ssh_password}' scp {self.download_path}/a.zip nvidia@172.16.2.14:/data/a.zip")




def get_diffpack_url(input_workflowId):





    pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python diff_pack_get.py <workflowId>")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    url = get_diffpack_url(workflow_id)
    if url:
        print(f"DiffPack Download URL: {url}")
    else:
        print("No DiffPack available for the given workflowId.")