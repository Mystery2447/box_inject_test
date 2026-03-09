import os
import sys
import json
import subprocess
import socket
import time

def execute(command: str) -> None:
        print(command)
        subprocess.run(command, shell=True)



def set_network(net:str):
    
    
    execute(f"sudo ip link add link {net} name mgbe3_0.5 type vlan id 5 >/dev/null 2>&1 || true")
    execute(f"sudo ip link set mgbe3_0.5 type vlan egress 0:2 1:2 2:2 3:2 4:2 5:2 6:2 7:2")
    execute(f"sudo ip address add 172.16.5.58/16 dev mgbe3_0.5 >/dev/null 2>&1 || true")
    execute(f"sudo ip link set dev mgbe3_0.5 address 02:47:57:4d:00:58")
    execute(f"sudo ip link set dev mgbe3_0.5 up")
    print("network setting complete...")


    
def inject_other_key():
    enter_EOL = "0a000301020311f1898e"
    enter_password = "13000301020388f807004445534159535638a4"
    other_key_mcu = "3C000301020266FA3000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5AC6A5945F16500911219129984BA8B387A06F24FE383CE4E81A73294065461B9CB3"
    other_key_soc = "3C0003010302B1C13000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5AC6A5945F16500911219129984BA8B387A06F24FE383CE4E81A73294065461B6F38"
    logout_EOL = "0a000301020322f22cee"

    target_ip = "172.16.5.15"
    target_port = 30065
    udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_sock.bind(("172.16.5.58",30065))
    udp_sock.settimeout(3)

    print("[LOG]:enter EOL mode,pls waiting...")
    udp_sock.sendto(bytes.fromhex(enter_EOL),(target_ip,target_port))
    udp_sock.recvfrom(512)
    time.sleep(0.5)
    print("[LOG]:unlock key...")
    udp_sock.sendto(bytes.fromhex(enter_password),(target_ip,target_port))
    udp_sock.recvfrom(512)
    time.sleep(0.5)
    print("[LOG]:inject default key...")
    udp_sock.sendto(bytes.fromhex(other_key_mcu),(target_ip,target_port))
    recv_data,recv_addr = udp_sock.recvfrom(512)
    print(f"recv data is {recv_data},from ip: {recv_addr}")
    recv_data = [format(a,"02x")for a in recv_data]
    if recv_data[12]=='01':
        print("[LOG]:inject mcu default key success!!!")
    else:
        print("[ERROR]:inject mcu deault key fail!!!")
    udp_sock.sendto(bytes.fromhex(other_key_soc),(target_ip,target_port))
    recv_data,recv_addr = udp_sock.recvfrom(512)
    print(f"recv data is {recv_data},from ip: {recv_addr}")
    recv_data = [format(a,"02x")for a in recv_data]
    if recv_data[12]=='01':
        print("[LOG]:inject soc default key success!!!")
    else:
        print("[ERROR]:inject soc deault key fail!!!")
    time.sleep(0.5)
    print("[LOG]:logout EOL mode...")
    udp_sock.sendto(bytes.fromhex(logout_EOL),(target_ip,target_port))
    time.sleep(0.5)
    udp_sock.close()
    print("[LOG]:inject default key success!!!pls reset ADCU.")
    ...



def inject_default_key():
    enter_EOL = "0a000301020311f1898e"
    enter_password = "13000301020388f807004445534159535638a4"
    default_key = "3c000301020266fa3000ffffffffffffffffffffffffffffffff5ac6a5945f16500911219129984ba8b387a06f24fe383ce4e81a73294065461b9cb3"
    logout_EOL = "0a000301020322f22cee"

    target_ip = "172.16.5.15"
    target_port = 30065
    udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_sock.bind(("172.16.5.58",30065))
    udp_sock.settimeout(3)

    print("[LOG]:enter EOL mode,pls waiting...")
    udp_sock.sendto(bytes.fromhex(enter_EOL),(target_ip,target_port))
    udp_sock.recvfrom(512)
    time.sleep(0.5)
    print("[LOG]:unlock key...")
    udp_sock.sendto(bytes.fromhex(enter_password),(target_ip,target_port))
    udp_sock.recvfrom(512)
    time.sleep(0.5)
    print("[LOG]:inject default key...")
    udp_sock.sendto(bytes.fromhex(default_key),(target_ip,target_port))
    recv_data,recv_addr = udp_sock.recvfrom(512)
    print(f"recv data is {recv_data},from ip: {recv_addr}")
    recv_data = [format(a,"02x")for a in recv_data]
    if recv_data[12]=='01':
        print("[LOG]:inject default key success!!!")
    else:
        print("[ERROR]:inject deault key fail!!!")
    time.sleep(0.5)
    print("[LOG]:logout EOL mode...")
    udp_sock.sendto(bytes.fromhex(logout_EOL),(target_ip,target_port))
    time.sleep(0.5)
    udp_sock.close()
    print("[LOG]:inject default key success!!!pls reset ADCU.")
    ...

if __name__ == "__main__":
    if len(sys.argv) >1:
        net = sys.argv[1]
        print(net)
    else:
        net = "enx207bd51a13cc"
        print("using default network card...")
    with open("/proc/net/dev") as f:
         if net not in f.read():
              print(f"[ERROR]:network card {net} don`t exist!!!check the network configuration")
              sys.exit(-1)

    set_network(net)
    inject_other_key()


    ...