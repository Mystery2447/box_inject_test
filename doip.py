import socket
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import cmac
import sys
from feishu import FeishuRobot
from ssh_client import SshClient
zip_path = "/data/a.zip"
sign_data=  "10fe416275706461746553656375726974794865616430000000000200000200000030020000be060000ee0800001008000037333065343166623265383435656132643335633536366264303833633462356138303362663863643336306338656631623963653864383937373433636662653336323362633963313736366633333764323839656536313030633133323066366463613430616631336463613634313533623232333966353538643539353334643364303336383938326439303032643838306436326236633632666235333764666566633161353339616139333461306438656137393538626165313062643864323237383431653436353866386161393430666162383235346331396661303236353138316635326261653165373461313936343737346538646334663531366331383533333338333539613133353338383132323265333135643736656262663339313531313466653037306431373833646331616162333636343339623237653432333632396232643237656237343132313337333132323039623662336331313833353137623131303265663531333436643762636539333931346634373862613261356432666632666465663035363031653865633037616132396465343938633261366665356239323762353732393963653032636565356564623033643130653638346436343566383164373434363330663666336431306433613463333030393433666164333534396139323330656361306530312d2d2d2d2d424547494e2043455254494649434154452d2d2d2d2d0d0a4d494945756a434341364b6741774942416749556370466d55544469717562486d6646616e58666d573368312f696f774451594a4b6f5a496876634e4151454c0d0a42514177675a4178466a415542674e5642414d4d44556c5056694250564545675533566951304578487a416442674e564241734d466b564649464e356333526c0d0a625342455a584e705a3234675247567764433478497a416842674e5642416f4d476b64795a57463049466468624777675457393062334967513238754c43424d0d0a644751754d517377435159445651514745774a44546a456a4d43454743537147534962334451454a4151775559336c695a584a7a5a574e31636d6c306555426e0d0a64323075593234774942634e4d6a41774e5441344d4467784e7a4533576867504d6a41314d4441314d4445774f4445334d5464614d476b784644415342674e560d0a42414d4d4330645854534250564546545355644f4d523877485159445651514c44425a465253425465584e305a5730675247567a615764754945526c634851750d0a4d534d77495159445651514b44427048636d56686443425859577873494531766447397949454e764c6977675448526b4c6a454c4d416b4741315545426777430d0a51303477676745694d4130474353714753496233445145424151554141344942447741776767454b416f4942415143363975546e4a696c5734722f4d383771460d0a31666f57626436776b526b744c465168337336777a76764562436d2b762b39456e702b3344502b416469573470646334665053333572757234385365424a6b410d0a2f6e795471736d584c615258736d307838383839795764322f4c53322f736f42624845577a704f5543654f7a316a714876446447317838516e556f6d736474690d0a6d53484245566f754e6a5964426a6b3774673131786b46735666534f7832653659426a503272345a484861674e6241464c4b314d662f694e43516950756459370d0a376747442f736156645241326576653330505257347a4c4b43414e54456f5a6d55596d2b735a4e32334c71516d45356468393344376a6d5246575770496c55730d0a2b534f433969673845664b7973415049682b38794b63664151673979677a733246556c626a35463270466d4743467438387276445a646b66394c53616759436a0d0a334f364c41674d424141476a676745754d4949424b6a414a42674e5648524d45416a41414d4173474131556444775145417749477744426e42674e56485334450d0a594442654d46796757714259686c5a6f644852774f6938764d5441754d6a55314c6a55794c6a45794e433955623342445153397764574a7361574d76615852790d0a64584e6a636d772f513045394e6b5577516a4a47516b4535516a644352444d30515551354d45464552454532515467784e45557a4e446b354d7a5532513051330d0a4d54426e42674e5648523845594442654d46796757714259686c5a6f644852774f6938764d5441754d6a55314c6a55794c6a45794e43395562334244515339770d0a64574a7361574d766158527964584e6a636d772f513045394e6b5577516a4a47516b4535516a644352444d30515551354d45464552454532515467784e45557a0d0a4e446b354d7a5532513051334d54416642674e5648534d454744415767425433694e58654b3854326a37526d3657732b36504b6535626273646a416442674e560d0a485134454667515552793855694f6c464f6743446641537563614d73787a356c363073774451594a4b6f5a496876634e4151454c425141446767454241432b390d0a644b73316a566d7743634a33414a42496e7a63327276366e5567764464377441327546526d6a4357456568575753334a4a555565593373726f4b646c6854304e0d0a6b6b436f2b384336386f4e4e41496b3630562b492f626173544c4c7255465441525a4f66597a654b5777515441576258377a472b6a6437446d554b6b487249450d0a71466b766e3964736a2f78474c6a4d4d7a43584264356b78693775596f45303266386a764a51787271384a55456a51384c5179444934666b68507838633035690d0a77305543616431624949395670364434746a6b7a793778333144434b497054464737693543366876396e46633943647371453738683947556162306361542f610d0a495146733470336445574161626564547957517071374c6b327073563672703748427649735a597148545446644b7038396f634b7265554c6b64356d633569460d0a587279445471395a61613765537772534949733d0d0a2d2d2d2d2d454e442043455254494649434154452d2d2d2d2d2d2d2d2d2d424547494e2043455254494649434154452d2d2d2d2d0d0a4d49494673444343424a6967417749424167495562677376757074373030725a4374326d7142546a535a4e577a5845774451594a4b6f5a496876634e4151454c0d0a42514177675a4578467a415642674e5642414d4d446b64585453424c54564e536232393049454e424d523877485159445651514c44425a465253425465584e300d0a5a5730675247567a615764754945526c634851754d534d77495159445651514b44427048636d56686443425859577873494531766447397949454e764c6977670d0a5448526b4c6a456a4d43454743537147534962334451454a4151775559336c695a584a7a5a574e31636d6c306555426e6432307559323478437a414a42674e560d0a42415954416b4e4f4d434158445449774d4455774f4441344d4441304e6c6f59447a49784d6a41774e4445304d4467774d445132576a43426b4445574d4251470d0a413155454177774e53553957494539555153425464574a44515445664d42304741315545437777575255556755336c7a644756744945526c63326c6e626942450d0a5a5842304c6a456a4d434547413155454367776152334a6c59585167563246736243424e623352766369424462793473494578305a433478437a414a42674e560d0a42415954416b4e4f4d534d774951594a4b6f5a496876634e41516b424442526a65574a6c636e4e6c5933567961585235514764336253356a626a4343415349770d0a4451594a4b6f5a496876634e4151454242514144676745504144434341516f4367674542414b336f2b49504458416b6b39315153497a366f692f6756702b5a2f0d0a72394c39357537464a42715559677a316645794d586c64315949544662533863593857447a4e736e4137314955496a71767338474a74637336725670344c78450d0a6b4d3279754e635054536c784e5a786933694f5642456a44382f755a53354c75664c7048793071665147526c4b6a514d72544e7a664d4561686c6b33703174550d0a744a6351504444736a3973753756347a50546756614e395633656353434453686a534c6a39366569455a784c6e733831714a4245794244717050694f425934540d0a3855426832345862475453664b724f316b38584a4959352b6a6e454453777a7974646f58484735706d734a66615a4634314c356537546d754268516a6f4a656f0d0a647964414e586c445052466751624a4a6b6f3869547a6f4137422f58336c2b5a783073474558646f6455613538705a484c7678446f6a534131714543417745410d0a41614f4341667377676748334d423047413155644467515742425433694e58654b3854326a37526d3657732b36504b6535626273646a416642674e5648534d450d0a474441576742524371796e474f59734b384f754f54482f626867567670335a544a44414d42674e5648524d45425441444151482f4d41344741315564447745420d0a2f77514541774942426a424b4267677242674546425163424151512b4d4477774f6759494b775942425155484d4147474c6d6830644841364c79395a623356790d0a58314e6c636e5a6c636c394f5957316c4f6c4276636e517656473977513045766247396b6346394359584e6c52453477667759494b77594242515548415173450d0a637a42784d4738474343734741515546427a4146686d4e6f644852774f6938764d5441754d6a55314c6a55794c6a45794e446f344d4467774c31527663454e420d0a4c33567a5a584a46626e4a7662477776593246445a584a3050324e6c636e52545a584a705957784f645731695a5849394e54466b4e446b325a544a6a4e7a55790d0a59324d304d4441344d7a686d4d7a4e695954686d4f5455314e5755775a4159445652307542463077577a425a6f46656756595a546148523063446f764c7a45770d0a4c6a49314e5334314d6934784d6a51364f4441344d433955623342445153397764574a7361574d766158527964584e6a636d772f513045394e54466b4e446b320d0a5a544a6a4e7a557959324d304d4441344d7a686d4d7a4e695954686d4f5455314e5755775a4159445652306642463077577a425a6f46656756595a54614852300d0a63446f764c7a45774c6a49314e5334314d6934784d6a51364f4441344d433955623342445153397764574a7361574d766158527964584e6a636d772f513045390d0a4e54466b4e446b325a544a6a4e7a557959324d304d4441344d7a686d4d7a4e695954686d4f5455314e5755774451594a4b6f5a496876634e4151454c425141440d0a676745424142545a4535764c3344644c50504e44353338324b71554d4d4d535076362b36666f364f4a494f32787a593566614b4b4f4a573559357a6a72452b520d0a58505065696d2b4661737251516b6761514a666b6d5a676a4c6941424c30484b46535a73715472576a6d6b33633768594874515769536a5035524f31415267430d0a7163796762634633314275612f35423452666a437556516836644175426f764b4a4757574f67595a4938357263324a684d4b643248736b35386d7671796c49370d0a39624778435a4472457568356345726779567762504b536f4e2b54563738344c4279597658785641524d4e7445584f7a4951414178733277744f72624e3061300d0a37374b79356b4d6c6538396374516f514770586d646d4168674571734e2f36794c326c71444647437152423551533969326f3648485a742f663334416a7934670d0a39577537514c383874787239563744646a36566c644d48423061773d0d0a2d2d2d2d2d454e442043455254494649434154452d2d2d2d2d"


def string_to_hex(data:str)->list:
    hex_list = [f"{ord(i):02x}" for i in data  ]
    
    return hex_list

class DoipClient:
    def __init__(self):
        self.target_ip = "172.16.2.14"
        self.test_address = 0x1001
        self.func_address = 0xE400
        self.SOC_address = 0x1110
        self.P2_time = 5
        self.S3_time = 5
        self.DOIP_TYPE_DIAGNOSTIC = 0x8001  # 诊断请求
        self.DOIP_TYPE_ALIVE_CHECK = 0x0005  # 路由激活请求
        self.other_key = bytes.fromhex("456E68616E636544475F6B65795F3132")
        self.default_key = bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
        self.mask = 0x2044434C
        self.car_type = ''
        self.sock_client = None

    def client_setup(self):
        """初始化 DOIP 连接"""
        self.sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_client.connect((self.target_ip, 13400))
        self.sock_client.settimeout(self.P2_time+1)
        print("doip_client setup init done")

    def build_doip_message(self, message_type, data: str = ''):
        """构建 DOIP 消息帧"""
        if not data:
            print("pls enter the data")
            return -1
        if len(data) % 2 != 0:
            print("error data format ,pls check it ")
            return -1

        doip_header = "02FD"
        frame = f"{self.test_address:04x}{self.SOC_address:04x}{data}"
        doip_len = f"{len(frame)//2:08x}"
        message_type_hex = f"{message_type:04x}"
        return f"{doip_header}{message_type_hex}{doip_len}{frame}"

    def sock_close(self):
        """关闭 DOIP 连接"""
        if self.sock_client:
            self.sock_client.close()
            print("DOIP connection close...")

    def recv_doip_message(self):
        """接收 DOIP 响应消息"""
        recv_data = self.sock_client.recv(256)
        recv_data = bytes.hex(recv_data)
        
        recv_data_1 = self.sock_client.recv(2048)

        if len(recv_data_1)>13:

            src_addr = int.from_bytes(recv_data_1[8:10], byteorder='big')
            dest_addr = int.from_bytes(recv_data_1[10:12], byteorder='big')

            UDS_data = recv_data_1[12:]
            
            # print("recv UDS data:{}".format(' '.join(['{:02x}'.format(i) for i in recv_data_1])))
            print("[recv UDS frame]:{}".format(' '.join(['0x{:02x}'.format(i) for i in UDS_data])))
            while UDS_data[0]==0x7f and UDS_data[2]==0x78:
                print("pending...")
                recv_data_1 = self.sock_client.recv(2048)
                UDS_data = recv_data_1[12:]
                print("[recv UDS frame]:{}".format(' '.join(['0x{:02x}'.format(i) for i in UDS_data])))
            return {
                'sid': int(UDS_data[0]),
                'data': [i for i in UDS_data[1:]],
                'len': len(UDS_data),
                'NRC':0
            }
        elif len(recv_data_1)==13:
            UDS_data = recv_data_1[12:]
            return {
                'sid': UDS_data[0],
                'data':UDS_data,
                'len': len(UDS_data),
                'NRC':UDS_data[2]
            }


    def route_active(self):
        """发送路由激活请求"""
        act_frame = f"02fd{self.DOIP_TYPE_ALIVE_CHECK:04x}0000000B{self.test_address:04x}E200000000FFFFFFFF"
        self.sock_client.sendall(bytes.fromhex(act_frame))
        self.sock_client.recv(512)
        print("routing active")

    def get_key(self, seed: list):
        """计算密钥（用于安全访问）"""
        real_seed = 0
        for data in seed:
            real_seed = (real_seed << 8) | data

        for _ in range(35):
            if real_seed & 0x80000000:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
                real_seed ^= self.mask
            else:
                real_seed = (real_seed << 1) & 0xFFFFFFFF
        return real_seed

    def aes128_cmac_generate_key(self, seed: bytes) -> bytes:
        """AES128-CMAC 生成密钥"""
        if len(self.default_key) != 16:
            raise ValueError("pincode必须是16字节长度")
        if len(seed) != 16:
            raise ValueError("seed必须是16字节长度")

        c = cmac.CMAC(algorithms.AES(self.default_key), backend=default_backend())
        c.update(seed)
        return c.finalize()

    def data_tansfer_ascii(self, data: list):
        """字节列表转 ASCII 字符串"""
        ascii_str = ''.join([chr(i) for i in data])
        print(ascii_str)
        return ascii_str

    def send_uds_req(self, SID: int, sub_func: int = None, data: str = None):
        """发送 UDS 请求"""
        uds_data = f"{SID:02x}"
        if sub_func is not None:
            uds_data += f"{sub_func:02x}"
        if data is not None:
            uds_data += data

        frame = self.build_doip_message(self.DOIP_TYPE_DIAGNOSTIC, uds_data)
        print(f"[Send data]:SID:0x{SID:02x},Data:{[uds_data[i:i+2] for i in range(2, len(uds_data), 2)]}")
        self.sock_client.send(bytes.fromhex(frame))
        return self.recv_doip_message()

    def DiagnosticSessionControl(self, session: int):
        """诊断会话控制"""
        self.send_uds_req(0x10, session)

    def hard_reset(self):
        """硬件复位"""
        self.send_uds_req(0x11, 0x01)

    def security_access(self, level: int):
        """安全访问（密钥验证）"""
        frame = self.send_uds_req(0x27, sub_func=level)
        seed = frame['data'][1:]

        if level == 0x01:
            self.mask = 0x2044434C
        elif level == 0x19:
            self.mask = 0x194C4344
        elif level == 0x29:
            self.mask = 0x294C4344
        elif level == 0x35:
            self.mask = 0x3644434C

        if frame['len'] - 2 == 4:
            key = self.get_key(seed)
            self.send_uds_req(0x27, level + 1, format(key, '08x'))
        elif frame['len'] - 2 == 16:
            key = self.aes128_cmac_generate_key(bytes(seed))
            self.send_uds_req(0x27, level + 1, key.hex().upper())
        else:
            print(f"[recv UDS frame]:{frame} without unlock")

    def DID_read(self,did:str):
        return self.send_uds_req(0x22,data=did)

    def DID_write(self, did: str, data: str):
        """写入 DID 数据"""
        if not isinstance(did, str):
            print("error type input!!!")
            return -1
        return self.send_uds_req(0x2e, data=(did + data))


    def RID_write(self,sub_fuc:int,rid=str,para:str=None):
        recv = None
        if para is not None:

           recv=  self.send_uds_req(0x31,sub_func=sub_fuc,data=rid+para)
        else:
           recv=  self.send_uds_req(0x31,sub_func=sub_fuc,data=rid)
        return recv

        """写入 F1B1 车型配置"""
    def write_F1B1_car_config_VIN(self):
        peizhizi_map = {
    # 基础配置 - 只需要第一个字节的
    "P03": "14000001" + "00" * 62,      # 8 + 124 = 132字符
    "P03A": "14000003" + "00" * 62,
    "P03-F": "1C000001" + "00" * 62,
    "P03A-F": "1C000003" + "00" * 62,
    "P02": "15000001" + "00" * 62,
    "P02A": "15000003" + "00" * 62,
    "D03B": "16000001" + "00" * 62,
    "D03A": "16000003" + "00" * 62,
    "D037": "23000000" + "00" * 62,
    "EC15": "0E000000" + "00" * 62,
    "EC15S": "1B000000" + "00" * 62,
    "C01-T": "17000000" + "00" * 62,
    "C062": "21000000" + "00" * 62,
    "C06A3": "22000000" + "00" * 62,
    "M81-3": "04000000" + "00" * 62,
    "M82": "05000000" + "00" * 62,
    "M83-1": "02000000" + "00" * 62,
    "M82-FZ": "11000000" + "00" * 62,
    "M81H": "2A000000" + "00" * 62,
    "C01": "03000000" + "00" * 62,
    "P01T": "24000003" + "00" * 62,
    "P01Z": "24000001" + "00" * 62,
    "DE061": "1A000700" + "00" * 62,
    "DE062": "1A000800" + "00" * 62,
    "DE06E": "27000000" + "00" * 62,
    "DE09": "06000000" + "00" * 62,
    "DE09U": "20000000" + "00" * 62,
    "DE09E": "28000000" + "00" * 62,
    "M81T": "2D000000" + "00" * 62,
    "M82T": "2E000000" + "00" * 62,
    "M83T": "2F000000" + "00" * 62,
    "B26": "0C000000" + "00" * 62,
    "B26E": "29000000" + "00" * 62,
    "B07": "2C000000" + "00" * 62,
    "B07E": "2B000000" + "00" * 62,
    
    # C061 - 第36字节(35)为20
    "C061": "1E 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # 第36字节为20 (36字节 = 34个00 + 2字符 = 35字节位置)
    "C062": "21 00 0D 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # C062 - 第3字节(2)为0D，第36字节(35)为40
    # C063 - 第3字节(2)为0C，第36字节(35)为40
    "C063": "1E 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C064 - 第3字节(2)为0D，第36字节(35)为40
    "C064": "1E 00 0D 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C06A1 - 第36字节(35)为20
    "C06A1": "1F 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # C06A2 - 第36字节(35)为40
    "C06A2": "1F 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A1 - 第16字节(15)为10，第36字节(35)为20
    "B26A1": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 10 00 10 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A3 - 第16字节(15)为00，第36字节(35)为20
    "B26A3": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A2 - 第16字节(15)为10，第36字节(35)为60
    "B26A2": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 10 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 60 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # B26A4 - 第16字节(15)为00，第36字节(35)为60
    "B26A4": "1D 00 0C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 60 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # DE07 - 第26字节(25)为01
    "DE07": "19 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 01 00 00 01 00 20 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # DE07 - 第26字节(25)为01
    
    # DE07U - 第26字节(25)为02
    "DE07U": "19 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 02 00 00 01 20 20 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""),
    
    # DE08 - 第26字节(25)为01
    "DE08": "18 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 01 00 00 01 80 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ",""), # DE08 - 第26字节(25)为01
    
    # DE08U - 第26字节(25)为02
    "DE08U": "18 00 00 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 01 40 00 00 00 00 00 00 00 02 00 00 01 80 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00".replace(" ","") # DE08U - 第26字节(25)为02,
    }
        if self.car_type not in peizhizi_map:
            print("[ERROR]!!! wrong car type!!! pls double check it")
            print("当前支持的车型对应配置字有：\n" + "\n".join([f"\t{k}" for k in peizhizi_map.keys()]))
            raise ValueError(f"未知的车型类型: {self.car_type}")

        peizhizi = peizhizi_map[self.car_type]
        self.DiagnosticSessionControl(0x03)
        self.security_access(0x01)
        self.DID_write("F190", "3837363534333231393837363534333231")
        resp = self.DID_write('F1B1', peizhizi)
        
        if resp["sid"] == 0x6e:
            self.hard_reset()
            print(f"[LOG]:write F1B1 car_type success!!!already reset ADCU for reloading car_type: {self.car_type}")
            return f"already inject car_type {self.car_type} and vin"
        else:
            print(f"[LOG]:write F1B1 car_type failed, resp: {resp}")
            return f"inject car_type {self.car_type} failed"

    def check_ota_progress(self):
        recv_frame  = self.DID_read("F1BA")
        status = recv_frame['data'][6]
        if status == 0x00:
            return {
                'progress':recv_frame['data'][7],
                'status':'success'
            }
        elif status ==0x01:
            return {
                'progress':recv_frame['data'][7],
                'status':'failed'
            }
        elif status ==0x02:
            return {
                'progress':recv_frame['data'][7],
                'status':'flashing'
            }
        elif status ==0x03:
            return {
                'progress':recv_frame['data'][7],
                'status':'noreq'
            }
        else:
            return{
                'status':'unknown',
                'progress':0
            }

    def check_guanzhuang_version(self):
        """通过 DOIP 读取罐装版本信息"""
        gwm_version_resp = self.send_uds_req(0x22, data="F189")
        gwm_software_resp = self.send_uds_req(0x22, data="F1BC")
        gwm_calib_resp = self.send_uds_req(0x22, data="F1C0")

        return {
            "gwm_version": self.data_tansfer_ascii(gwm_version_resp.get('data')[2:]),
            "gwm_software_infomation": self.data_tansfer_ascii(gwm_software_resp.get('data')[2:]),
            "gwm_Calibration_version": self.data_tansfer_ascii(gwm_calib_resp.get('data')[2:])
        }
    
    

    def THOR_ota_a_zip(self):
        """OTA_fuc"""
        global zip_path,sign_data
        self.DiagnosticSessionControl(0x03)
        resp = self.security_access(0x01)
        print(resp)
        time.sleep(1)
        self.RID_write(0x01,"0216",(f"{len(zip_path):04x}"+''.join(string_to_hex(zip_path))))
        self.RID_write(0x01,"0202")
        self.DiagnosticSessionControl(0x02)
        resp = self.security_access(0x35)
        print(resp)
        self.DID_write("f0ff","250115153036ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
        self.RID_write(0x01,"0210","ffff04ffffffffffffffffffffffffffffffffffff")
        self.RID_write(0x01,"0215",(f'{len(zip_path):04x}'+''.join(string_to_hex(zip_path))+sign_data))
        self.RID_write(0x01,"0211","ffffffffffffffffffffffffffffffff")
        self.RID_write(0x01,"0212")
        self.RID_write(0x01,"0208")
        progress = self.check_ota_progress()

        while progress['progress']!=98 and progress['status']=='flashing':
            time.sleep(5)
            progress = self.check_ota_progress()
            print(progress)
        if progress['progress']==98 and progress['status']=='flashing':
            for i in range(60,0,-1):
                time.sleep(1)
                print(f"ADCU reset...cnt down:{i}s ",end='')
            self.client_setup()
            self.route_active()
            progress = self.check_ota_progress()

            print(f"fota progress:{progress['progress']},status:{progress['status']}")
            if progress['progress']==100:
                return 0
        else:
            return progress

    def ORIN_ota_a_zip(self):
        """OTA_fuc"""
        global zip_path,sign_data
        self.DiagnosticSessionControl(0x03)
        resp = self.security_access(0x19)
        print(resp)
        self.RID_write(0x01,"0216",(f"{len(zip_path):04x}"+''.join(string_to_hex(zip_path))))
        resp = self.security_access(0x01)
        print(resp)
        self.RID_write(0x01,"0202")
        self.DiagnosticSessionControl(0x02)
        resp = self.security_access(0x35)
        print(resp)
        self.DID_write("f0ff","250115153036ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
        # self.DiagnosticSessionControl(0x01)
        # self.DiagnosticSessionControl(0x03)
        # self.security_access(0x19)
        self.RID_write(0x01,"0210","ffff04ffffffffffffffffffffffffffffffffffff")

        resp = self.security_access(0x29)
        print(resp)
        self.RID_write(0x01,"0215",(f'{len(zip_path):04x}'+''.join(string_to_hex(zip_path))+sign_data))
        resp = self.security_access(0x35)
        print(resp)
        self.RID_write(0x01,"0211","ffffffffffffffffffffffffffffffff")
        resp = self.security_access(0x29)
        self.RID_write(0x01,"0212")
        self.RID_write(0x01,"0208")
        progress = self.check_ota_progress()

        while progress['progress']!=98 and progress['status']=='flashing':
            time.sleep(3.5)
            progress = self.check_ota_progress()
            print(progress)
        if progress['progress']==98 and progress['status']=='flashing':
            for i in range(60,0,-1):
                time.sleep(1)
                print(f"ADCU reset...cnt down:{i}s ",end='')
            self.client_setup()
            self.route_active()
            progress = self.check_ota_progress()

            print(f"fota progress:{progress['progress']},status:{progress['status']}")
            if progress['progress']==100:
                return 0
        else:
            return progress





if __name__=='__main__':
    if len(sys.argv)>1:
        cartype = sys.argv[1]
        print(f"recv architect is {cartype}")
    else:
        cartype = 'ORINX'  
    feishu_test = FeishuRobot("https://open.feishu.cn/open-apis/bot/v2/hook/86f13735-aa8e-4dc1-aa6a-258177111a1e")
    test = DoipClient()
    test.car_type = cartype
    test.client_setup()
    test.route_active()
    if cartype in ('ORINX','ORINY'):
        ret = test.ORIN_ota_a_zip()
    elif cartype =='THOR':
        ret = test.THOR_ota_a_zip()
    if ret ==0:
        feishu_test.send_text("OTA success")
    else:
        feishu_test.send_text(f"OTA FAIL,progress:{ret}")
    test.sock_close()
