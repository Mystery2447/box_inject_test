import paramiko
import time
import argparse

class SSHRemoteController:
    def __init__(self, hostname, username, password=None, key_path=None):
        """
        初始化SSH控制器
        
        Args:
            hostname: 远程机器IP
            username: SSH用户名
            password: SSH密码（可选，与key_path二选一）
            key_path: SSH私钥路径（可选，与password二选一）
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = key_path
        self.ssh_client = None
        self.shell = None
        
    def connect(self):
        """建立SSH连接"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"正在连接到 {self.hostname}...")
            if self.key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.key_path)
                self.ssh_client.connect(
                    hostname=self.hostname,
                    username=self.username,
                    pkey=private_key,
                    timeout=10
                )
            else:
                self.ssh_client.connect(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            print("✅ SSH连接成功！")
            return True
        except Exception as e:
            print(f"❌ SSH连接失败: {e}")
            return False
    
    def send_serial_commands(self, serial_port, commands, baudrate=115200):
        """
        发送命令到串口并显示输出
        
        Args:
            serial_port: 串口设备路径，如 '/dev/ttyUSB0'
            commands: 命令列表或单个命令字符串
            baudrate: 波特率，默认115200
        """
        if not self.ssh_client:
            print("❌ 未建立SSH连接")
            return False
        
        if not commands:
            print("⚠️ 没有要发送的串口命令")
            return False
        
        # 如果commands是字符串，转换为列表
        if isinstance(commands, str):
            commands = [commands]
        
        try:
            # 创建交互式shell（用于发送命令）
            if not self.shell:
                self.shell = self.ssh_client.invoke_shell()
                time.sleep(2)
            
            print(f"\n📡 开始发送串口命令到 {serial_port}:")
            
            for command in commands:
                # 发送命令到串口
                send_cmd = f'echo -e "{command}" > {serial_port}\n'
                self.shell.send(send_cmd)
                print(f"  ✓ 已发送: {command.strip()}")
                time.sleep(0.5)
                
                # 读取串口响应（可选）
                # 注意：某些串口设备可能不会立即响应
                read_cmd = f'timeout 2 cat {serial_port} 2>/dev/null || echo "无响应"'
                stdin, stdout, stderr = self.ssh_client.exec_command(read_cmd)
                raw = stdout.read()

                if raw:
                    text = raw.decode('utf-8', errors='ignore')  # ✅ 关键
                    print(f"  📥 串口响应: {text.strip()}")
                else:
                    print("  ⚠️ 没有从串口收到响应")
                    return False
            print("✅ 串口命令发送完成\n")
            return True
            
        except Exception as e:
            print(f"❌ 发送串口命令失败: {e}")
            return False
    
    def execute_python_script(self, script_path, args=None):
        if not self.ssh_client:
            print("❌ 未建立SSH连接")
            return False
        
        if not script_path:
            print("❌ 未指定脚本路径")
            return False
        
        try:
            # ✅ 强制无缓冲
            cmd = f'python3 -u {script_path}'
            if args:
                cmd += f' {args}'
            
            print(f"\n🐍 执行Python脚本: {script_path}")
            if args:
                print(f"📝 脚本参数: {args}")
            print("-" * 60)
            
            # ✅ 开启PTY（非常关键）
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd, get_pty=True)
            
            print("📤 脚本输出:")
            
            # ✅ 实时读 stdout
            for line in iter(stdout.readline, ""):
                if line:
                    print(f"  {line.rstrip()}")
            
            # ✅ 实时读 stderr（不要用 read）
            for line in iter(stderr.readline, ""):
                if line:
                    print(f"❌ {line.rstrip()}")
            
            print("-" * 60)
            print("✅ 脚本执行完成\n")
            return True
            
        except Exception as e:
            print(f"❌ 执行脚本失败: {e}")
            return False    
    def execute_custom_command(self, command):
        """
        执行自定义shell命令并显示输出
        
        Args:
            command: 要执行的命令
        """
        if not self.ssh_client:
            print("❌ 未建立SSH连接")
            return None
        
        try:
            print(f"\n💻 执行命令: {command}")
            print("-" * 60)
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            # 实时读取输出
            for line in iter(stdout.readline, ""):
                if line:
                    print(f"  {line.rstrip()}")
            
            error = stderr.read().decode()
            if error:
                print(f"\n❌ 错误信息:")
                print(f"  {error}")
                return None
            
            print("-" * 60)
            return True
            
        except Exception as e:
            print(f"❌ 执行命令失败: {e}")
            return None
    
    def close(self):
        """关闭SSH连接"""
        if self.shell:
            self.shell.close()
        if self.ssh_client:
            self.ssh_client.close()
            print("🔌 SSH连接已关闭\n")