import requests
import os
import sys
API_BASE_URL = "https://prod-artifacts-server.srv.deeproute.cn"
API_TOKEN = "Bearer adas-farm_77868_+ae2dmmu48degsjfayynp2n9o5ca3bbr"
DOWNLOAD_PATH = "/tmp/diff_pack_download"

class DiffPackClient:
    def __init__(self,Architecture=None,workflow_id=None):
        self.architecture = Architecture
        self.switch_en = False
        if self.architecture is None:
            self.ssh_password = "#7F7d8or"
        elif self.architecture == 'ORINX':
            self.ssh_password = "W8k3L2@m;"
        elif self.architecture == "ORINY":
            self.ssh_password = "#7F7d8or"
        elif self.architecture == "THOR":
            self.ssh_password = "G7#kL2@m"
            self.switch_en = True
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
        if url is None:
            print("No diffpack URL found.")
            raise ValueError("No diffpack URL found.")
        os.system(f"wget -O {self.download_path}/a.zip '{url}' --no-check-certificate")

    def scp_diffpack(self):
        # os.system(f"sshpass -p '{self.ssh_password}' scp {self.download_path}/a.zip nvidia@172.16.2.14:/data/a.zip")
        os.system(f"sshpass -p '{self.ssh_password}' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.download_path}/a.zip nvidia@172.16.2.14:/data/a.zip")
    def get_injectpack_uuid(self):
        # Implementation for getting injectpack UUID
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        uuid = resp.json().get('data').get("uuid")
        print(f"原始 API 响应数据: {uuid}")
        return uuid
    def get_injectpack_info(self):
        # Implementation for getting injectpack info
        headers = {
                'Authorization': API_TOKEN,
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        filter_driver = {"fullName":"sourceDriver",
                         "gwmShortName":"sourceDriver",
                         "packageName":"sourceDsvSoc",            
                         }
        filter_mcu = {
                            "uuid":"sourceMcu",
                            "packageName":"sourceMcu",  
        }
        filter_switch = {
                            "uuid":"sourceSwitch",
                            "packageName":"sourceSwitch",   
        }
        resp = requests.get(f"{API_BASE_URL}/api/v2/workflows/integration/{self.workflow_id}", headers=headers, verify=False,data=None)
        resp.raise_for_status()
        raw_data = resp.json().get('data').get("sourceFOTA")
        # print(f"原始 API 响应数据: {raw_data}")
        if(self.switch_en):
            ret = {
                "mcu":{
                    "uuid":raw_data.get("sourceMcu",{}).get("uuid"),
                    "packageName":raw_data.get("sourceMcu",{}).get("packageName"),
                },
                "switch":{
                    "uuid":raw_data.get("sourceSwitch",{}).get("uuid"),
                    "packageName":raw_data.get("sourceSwitch",{}).get("packageName"),
                },
                "switchb":{
                    "uuid":raw_data.get("sourceSwitchB",{}).get("uuid"),
                    "packageName":raw_data.get("sourceSwitchB",{}).get("packageName"),
                },
                "driver":{
                    "fullName":raw_data.get("sourceDriver",{}).get("fullName"),
                    "gwmShortName":raw_data.get("sourceDriver",{}).get("gwmShortName"),
                    "socVersion":raw_data.get("sourceSoc").get("sourceDsvSoc",{}).get("packageName"),
                }
            }
        else:
            ret = {
                "mcu":{
                    "uuid":raw_data.get("sourceMcu",{}).get("uuid"),
                    "packageName":raw_data.get("sourceMcu",{}).get("packageName"),
                },
                "switch":{
                    "uuid":raw_data.get("sourceSwitch",{}).get("uuid"),
                    "packageName":raw_data.get("sourceSwitch",{}).get("packageName"),
                },
                "driver":{
                    "fullName":raw_data.get("sourceDriver",{}).get("fullName"),
                    "gwmShortName":raw_data.get("sourceDriver",{}).get("gwmShortName"),
                    "socVersion":raw_data.get("sourceSoc").get("sourceDsvSoc",{}).get("packageName"),
                }
            }
        print(f"injectpack info: {ret}")
        return ret



def test():
    client = DiffPackClient(Architecture="THOR", workflow_id="86ebf5be-f311-4a2f-9df2-dbc0617cffc4")
    client.get_injectpack_info()
    client.get_injectpack_uuid()


if __name__ == "__main__":
    test()
    # if len(sys.argv) != 2:
    #     print("Usage: python diff_pack_get.py <workflowId>")
    #     sys.exit(1)
    
    # workflow_id = sys.argv[1]
    # client = DiffPackClient(Architecture="THOR", workflow_id=workflow_id)
    # client.download_diffpack(client.get_diffpack_url())
